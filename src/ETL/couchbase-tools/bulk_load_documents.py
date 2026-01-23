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
from couchbase.options import ClusterOptions


def get_cluster(username, password, endpoint):
    options = ClusterOptions(PasswordAuthenticator(username, password))
    cluster = Cluster(endpoint, options)
    cluster.wait_until_ready(timedelta(seconds=5))
    return cluster


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

    logger.info(f"Starting bulk load from {args.file.name}")
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
            result = collection.insert_multi(documents)
            elapsed_time = time.perf_counter() - start_time
            logger.info(f"Uploaded {len(result.results)} documents in {elapsed_time:.2f} seconds")

            success_upload += len(result.results)
            failed_upload += len(result.exceptions)

            if result.exceptions:
                logger.warning(f"Failed to upload {len(result.exceptions)} documents in this batch")
                for key, exception in result.exceptions.items():
                    logger.debug(f"Failed document key: {key}, error: {exception}")

            del documents
            documents = {}
            start_time = time.perf_counter()

    if documents:
        result = collection.insert_multi(documents)
        elapsed_time = time.perf_counter() - start_time
        logger.info(f"Uploaded {len(result.results)} documents in {elapsed_time:.2f} seconds")

        success_upload += len(result.results)
        failed_upload += len(result.exceptions)

        if result.exceptions:
            logger.warning(f"Failed to upload {len(result.exceptions)} documents in final batch")
            for key, exception in result.exceptions.items():
                logger.debug(f"Failed document key: {key}, error: {exception}")

    logger.info(f"Successfully uploaded {success_upload} documents")

    if failed_upload:
        logger.warning(f"Failed to upload {failed_upload} documents")

    logger.info("Bulk load completed")


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
        help="Set the number of document per batch (default: 10000)"
    )

    args = parser.parse_args()
    main(args)
