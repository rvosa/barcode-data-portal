"""
use:
    python bulk_remove_documents.py --username user --password 'password' --endpoint couchbase://localhost --file ids.txt
    python bulk_remove_documents.py --username user --password 'password' --endpoint couchbase://localhost --bucket bucket --scope _default --collection _default --file ids.txt
"""

import argparse
import logging
import sys
import time
from datetime import timedelta

from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.exceptions import AmbiguousTimeoutException, TimeoutException
from couchbase.options import ClusterOptions, ClusterTimeoutOptions

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

_BATCH_SIZE = 10000
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2
_KV_TIMEOUT_SECONDS = 30


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


def remove_with_retry(collection, ids, max_retries=_MAX_RETRIES):
    """Remove documents with retry logic for transient timeout errors."""
    remaining_ids = ids.copy()
    all_results = {}
    all_exceptions = {}

    for attempt in range(max_retries):
        if not remaining_ids:
            break

        result = collection.remove_multi(remaining_ids)
        all_results.update(result.results)

        # Check for timeout exceptions that can be retried
        retry_ids = []
        for key, exc in result.exceptions.items():
            if isinstance(exc, (AmbiguousTimeoutException, TimeoutException)):
                logger.warning(
                    f"Timeout on attempt {attempt + 1}/{max_retries} for key: {key}"
                )
                retry_ids.append(key)
            else:
                all_exceptions[key] = exc

        if retry_ids and attempt < max_retries - 1:
            delay = _RETRY_DELAY_SECONDS * (2**attempt)
            logger.info(f"Retrying {len(retry_ids)} documents after {delay}s delay")
            time.sleep(delay)
            remaining_ids = retry_ids
        else:
            # Final attempt - add remaining timeout exceptions
            for key in retry_ids:
                logger.error(f"Failed after {max_retries} retries for key: {key}")
                all_exceptions[key] = result.exceptions[key]
            break

    return type("MultiResult", (), {"results": all_results, "exceptions": all_exceptions})()


def main(args):
    cluster = get_cluster(args.username, args.password, args.endpoint)
    bucket = cluster.bucket(args.bucket)
    scope = bucket.scope(args.scope)
    collection = scope.collection(args.collection)

    ids = []
    success_remove = 0
    failed_remove = 0
    start_time = time.perf_counter()
    for id in args.file:
        ids.append(id.strip())

        if len(ids) >= _BATCH_SIZE:
            result = remove_with_retry(collection, ids)
            print(
                f"Removed {len(result.results)}\t{time.perf_counter() - start_time}",
                file=sys.stderr,
            )
            success_remove += len(result.results)
            failed_remove += len(result.exceptions)

            del ids
            ids = []
            start_time = time.perf_counter()

    if ids:
        result = remove_with_retry(collection, ids)
        print(
            f"Removed {len(result.results)}\t{time.perf_counter() - start_time}",
            file=sys.stderr,
        )
        success_remove += len(result.results)
        failed_remove += len(result.exceptions)

    print(f"Successfully Removed {success_remove}", file=sys.stderr)

    if failed_remove:
        print(
            f"Failed to Remove {failed_remove}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--username", required=True, type=str)
    parser.add_argument("--password", required=True, type=str)
    parser.add_argument("--endpoint", required=True, type=str)

    parser.add_argument("--bucket", default="BCDM", type=str)
    parser.add_argument("--scope", default="_default", type=str)
    parser.add_argument("--collection", default="primary", type=str)

    parser.add_argument(
        "--file",
        required=True,
        type=argparse.FileType("r"),
        help="File containing one ID per line.",
    )

    args = parser.parse_args()
    main(args)
