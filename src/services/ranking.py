from fastapi import APIRouter, Path
from typing import Dict, Optional

import pathlib
import sys

try:
    import dao
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao


route = APIRouter(tags=["ranking"])


def get_cb_ranking_by_processid(processid: str) -> Optional[Dict]:
    """
    Retrieve ranking data for a specific processid from the specimen_ranks collection.

    Uses processid as the document key (primary key) for direct lookup.
    """
    bucket = dao.NAME_MAP["specimen_ranks"]["bucket"]
    collection = dao.NAME_MAP["specimen_ranks"]["collection"]

    cluster = dao._get_cb_cluster()
    cb_bucket = cluster.bucket(bucket)
    cb_collection = cb_bucket.default_collection()

    # Since processid is the primary key, we can do a direct key lookup
    # However, the collection might use a different scope, so we query instead
    query = f"""
        SELECT `{collection}`.*
        FROM `{bucket}`.`_default`.`{collection}`
        WHERE processid = $processid
    """

    try:
        result = cluster.query(query, processid=processid)
        rows = list(result.rows())
        if rows:
            return rows[0]
    except Exception:
        pass

    return None


@route.get(
    "/ranking/{processid}",
    response_model=Optional[Dict],
    response_description="Ranking data for a specimen record",
)
async def get_ranking(
    processid: str = Path(title="Process ID of the specimen record"),
):
    """
    Retrieve BOLDetective ranking data for a specimen record.

    Returns ranking information including:
    - **rank**: Quality rank (1-7, where 1 is best)
    - **sumscore**: Sum of all criteria scores
    - **criteria**: Individual criterion pass/fail scores

    Returns null if ranking data is not available for the specified processid.
    """
    ranking = get_cb_ranking_by_processid(processid)
    return ranking
