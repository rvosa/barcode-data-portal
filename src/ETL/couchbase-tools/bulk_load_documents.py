"""
use:
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --file documents.jsonl
    python bulk_load_documents.py --username user --password 'password' --endpoint couchbase://localhost --primary-key key --bucket bucket --scope _default --collection _default --file documents.jsonl
"""

import argparse
import logging
import sys
import time
import ujson
from collections import namedtuple
from datetime import timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.exceptions import AmbiguousTimeoutException, TimeoutException
from couchbase.options import ClusterOptions, ClusterTimeoutOptions

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10000
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2
_KV_TIMEOUT_SECONDS = 30

MultiResult = namedtuple("MultiResult", ["results", "exceptions"])


def get_cluster(username, password, endpoint):
    options = ClusterOptions(
        PasswordAuthenticator(username, password),
        timeout_options=ClusterTimeoutOptions(
            kv_timeout=timedelta(seconds=_KV_TIMEOUT_SECONDS),
        ),
    )
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=30))
    return cluster


def insert_with_retry(collection, documents, max_retries=_MAX_RETRIES):
    """Insert documents with retry logic for transient timeout errors."""
    remaining_docs = documents.copy()
    all_results = {}
    all_exceptions = {}

    for attempt in range(max_retries):
        if not remaining_docs:
            break

        result = collection.insert_multi(remaining_docs)
        all_results.update(result.results)

        # Check for timeout exceptions that can be retried
        retry_docs = {}
        for key, exc in result.exceptions.items():
            if isinstance(exc, (AmbiguousTimeoutException, TimeoutException)):
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{max_retries} for key: {key}"
                )
                retry_docs[key] = remaining_docs[key]
            else:
                all_exceptions[key] = exc

        if retry_docs and attempt < max_retries - 1:
            delay = _RETRY_DELAY_SECONDS * (2**attempt)
            logger.info(f"Retrying {len(retry_docs)} documents after {delay}s delay")
            time.sleep(delay)
            remaining_docs = retry_docs
        else:
            # Final attempt - add remaining timeout exceptions
            for key in retry_docs:
                logger.error(f"Failed after {max_retries} retries for key: {key}")
                all_exceptions[key] = result.exceptions[key]
            break

    return MultiResult(results=all_results, exceptions=all_exceptions)


def main(args):
    cluster = get_cluster(args.username, args.password, args.endpoint)
    bucket = cluster.bucket(args.bucket)
    scope = bucket.scope(args.scope)
    collection = scope.collection(args.collection)

    documents = {}
    success_upload = 0
    failed_upload = 0
    start_time = time.perf_counter()
    for document in args.file:
        document = ujson.loads(document)
        if args.primary_key not in document:
            failed_upload += 1
            continue
        key = str(document[args.primary_key])
        documents[key] = document

        if len(documents) >= _BATCH_SIZE:
            result = insert_with_retry(collection, documents)
            print(
                f"Uploaded {len(result.results)}\t{time.perf_counter() - start_time}",
                file=sys.stderr,
            )
            success_upload += len(result.results)
            failed_upload += len(result.exceptions)

            del documents
            documents = {}
            start_time = time.perf_counter()

    if documents:
        result = insert_with_retry(collection, documents)
        print(
            f"Uploaded {len(result.results)}\t{time.perf_counter() - start_time}",
            file=sys.stderr,
        )
        success_upload += len(result.results)
        failed_upload += len(result.exceptions)

    print(f"Successfully Uploaded {success_upload}", file=sys.stderr)

    if failed_upload:
        print(
            f"Failed to Upload {failed_upload}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)
    parser.add_argument("--primary-key", required=True, type=str)

    parser.add_argument("--bucket", default="BCDM", type=str)
    parser.add_argument("--scope", default="_default", type=str)
    parser.add_argument("--collection", default="primary", type=str)

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one document per line.",
    )

    args = parser.parse_args()
    main(args)
