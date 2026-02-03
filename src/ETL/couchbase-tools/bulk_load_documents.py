"""
use:
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --file documents.jsonl
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --bucket bucket --scope _default --collection _default --file documents.jsonl
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --file documents.jsonl --verbosity DEBUG
"""

import argparse
import logging
import sys
import time
import ujson
from datetime import timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.exceptions import CouchbaseException
from couchbase.options import ClusterOptions, ClusterTimeoutOptions

_BATCH_SIZE = 10000
_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 2  # seconds (base delay, will increase with backoff)


class MultiResultWrapper:
    """Wrapper to provide consistent interface for aggregated multi-operation results."""

    def __init__(self, results, exceptions):
        self.results = results
        self.exceptions = exceptions


def get_cluster(username, password, endpoint):
    """Create cluster connection with extended timeouts for bulk operations."""
    timeout_opts = ClusterTimeoutOptions(
        kv_timeout=timedelta(seconds=10),  # increased from default 2.5s
    )
    options = ClusterOptions(
        PasswordAuthenticator(username, password),
        timeout_options=timeout_opts
    )
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=10))
    return cluster


def _insert_multi_with_retry(collection, documents, logger):
    """
    Execute insert_multi with retry logic for individual document failures.

    Unlike the previous implementation which only caught batch-level exceptions,
    this handles the case where insert_multi returns successfully but with
    individual document failures in result.exceptions.
    """
    remaining = documents.copy()
    all_results = {}
    all_exceptions = {}

    for attempt in range(_RETRY_ATTEMPTS):
        if not remaining:
            break

        try:
            result = collection.insert_multi(remaining)
            all_results.update(result.results)

            if result.exceptions:
                failed_count = len(result.exceptions)
                if attempt < _RETRY_ATTEMPTS - 1:
                    # Retry only the failed documents
                    delay = _RETRY_DELAY * (attempt + 1)  # exponential backoff
                    logger.info(
                        f"Attempt {attempt + 1}/{_RETRY_ATTEMPTS}: {failed_count} document failures, "
                        f"retrying in {delay}s..."
                    )
                    for key, exc in result.exceptions.items():
                        logger.debug(f"  Failed: {key} - {type(exc).__name__}")

                    # Build retry set from only failed documents
                    remaining = {k: documents[k] for k in result.exceptions.keys()}
                    time.sleep(delay)
                else:
                    # Final attempt - record all remaining failures
                    logger.warning(
                        f"Attempt {attempt + 1}/{_RETRY_ATTEMPTS}: {failed_count} documents "
                        f"failed after all retries"
                    )
                    all_exceptions.update(result.exceptions)
                    remaining = {}
            else:
                # All documents in this batch succeeded
                remaining = {}

        except CouchbaseException as e:
            # Entire batch failed (network issue, cluster problem, etc.)
            if attempt < _RETRY_ATTEMPTS - 1:
                delay = _RETRY_DELAY * (attempt + 1)
                logger.warning(
                    f"Batch-level failure on attempt {attempt + 1}/{_RETRY_ATTEMPTS}: "
                    f"{type(e).__name__} - {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Batch-level failure after all {_RETRY_ATTEMPTS} attempts: {e}"
                )
                raise

    return MultiResultWrapper(all_results, all_exceptions)


def main(args):
    # Configure logging
    numeric_level = getattr(logging, args.verbosity.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid verbosity level: {args.verbosity}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    logger = logging.getLogger(__name__)

    logger.debug(f"Connecting to {args.endpoint}")
    cluster = get_cluster(args.username, args.password, args.endpoint)
    bucket = cluster.bucket(args.bucket)
    scope = bucket.scope(args.scope)
    collection = scope.collection(args.collection)

    documents = {}
    success_upload = 0
    failed_upload = 0
    start_time = time.perf_counter()
    batch_size = args.batch_size
    batch_count = 0

    logger.info(f"Starting bulk load from {args.file.name}")
    logger.info(f"Target: {args.bucket}.{args.scope}.{args.collection}")
    logger.debug(f"Batch size: {batch_size}")

    for document in args.file:
        document = ujson.loads(document)
        if args.primary_key not in document:
            failed_upload += 1
            logger.warning(f"Document missing primary key '{args.primary_key}'")
            continue
        key = str(document[args.primary_key])
        documents[key] = document

        if len(documents) >= batch_size:
            batch_count += 1
            result = _insert_multi_with_retry(collection, documents, logger)
            elapsed = time.perf_counter() - start_time
            docs_per_sec = len(result.results) / elapsed if elapsed > 0 else 0

            logger.info(
                f"Batch {batch_count}: uploaded {len(result.results)} docs in {elapsed:.2f}s "
                f"({docs_per_sec:.0f} docs/sec)"
            )
            success_upload += len(result.results)
            failed_upload += len(result.exceptions)

            if result.exceptions:
                logger.warning(f"Batch {batch_count}: {len(result.exceptions)} documents failed after retries")
                for key, exception in result.exceptions.items():
                    logger.debug(f"  Permanent failure - key: {key}, error: {exception}")

            del documents
            documents = {}
            start_time = time.perf_counter()

    # Handle final partial batch
    if documents:
        batch_count += 1
        result = _insert_multi_with_retry(collection, documents, logger)
        elapsed = time.perf_counter() - start_time
        docs_per_sec = len(result.results) / elapsed if elapsed > 0 else 0

        logger.info(
            f"Batch {batch_count} (final): uploaded {len(result.results)} docs in {elapsed:.2f}s "
            f"({docs_per_sec:.0f} docs/sec)"
        )
        success_upload += len(result.results)
        failed_upload += len(result.exceptions)

        if result.exceptions:
            logger.warning(f"Batch {batch_count}: {len(result.exceptions)} documents failed after retries")
            for key, exception in result.exceptions.items():
                logger.debug(f"  Permanent failure - key: {key}, error: {exception}")

    # Summary
    logger.info(f"{'=' * 50}")
    logger.info(f"Bulk load completed: {success_upload} succeeded, {failed_upload} failed")

    if failed_upload:
        logger.warning(f"Failed to upload {failed_upload} documents - check DEBUG logs for details")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bulk load JSON documents into Couchbase",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--username", required=True, type=str, help="Couchbase username")
    parser.add_argument("--password", required=True, type=str, help="Couchbase password")
    parser.add_argument("--endpoint", required=True, type=str, help="Couchbase endpoint (e.g., couchbase://localhost)")
    parser.add_argument("--primary-key", required=True, type=str, help="Field name to use as document key")

    parser.add_argument("--bucket", default="BCDM", type=str, help="Couchbase bucket name (default: BCDM)")
    parser.add_argument("--scope", default="_default", type=str, help="Couchbase scope (default: _default)")
    parser.add_argument("--collection", default="primary", type=str, help="Couchbase collection (default: primary)")

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one document per line (JSONL format)"
    )

    parser.add_argument(
        "--verbosity",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging verbosity level (default: INFO)"
    )

    parser.add_argument(
        "--batch-size",
        default=10000,
        type=int,
        help="Set the number of documents per batch (default: 10000)"
    )

    args = parser.parse_args()
    main(args)