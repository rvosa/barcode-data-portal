from fastapi import APIRouter, Path
from pydantic import BaseModel
from typing import Dict, Optional
import logging

import pathlib
import sys

try:
    import dao
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import dao

logger = logging.getLogger(__name__)

route = APIRouter(tags=["ranking"])


class RankingCriteria(BaseModel):
    """Individual BOLDetective criteria scores (1 = pass, 0 = fail)."""
    species_level_id: int = 0
    bin_assigned: int = 0
    sequence_quality: int = 0
    type_status: int = 0
    has_image: int = 0
    identifier_named: int = 0
    id_method_morphological: int = 0
    country_present: int = 0
    coords_present: int = 0
    collection_date_present: int = 0
    collector_present: int = 0
    locality_present: int = 0
    institution_public: int = 0
    museum_id_present: int = 0
    voucher_status: int = 0


class RankingResponse(BaseModel):
    """BOLDetective ranking data for a specimen record."""
    processid: str
    rank: int
    sumscore: int
    criteria: RankingCriteria


def get_cb_ranking_by_processid(processid: str) -> Optional[Dict]:
    """
    Retrieve ranking data for a specific processid from the specimen_ranks collection.

    Uses a N1QL query to fetch the ranking document.
    """
    bucket = dao.NAME_MAP["specimen_ranks"]["bucket"]
    collection = dao.NAME_MAP["specimen_ranks"]["collection"]

    cluster = dao._get_cb_cluster()

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
    except Exception as e:
        logger.warning(f"Error fetching ranking for processid {processid}: {e}")

    return None


@route.get(
    "/ranking/{processid}",
    response_model=Optional[RankingResponse],
    response_description="Ranking data for a specimen record",
)
async def get_ranking(
    processid: str = Path(title="Process ID of the specimen record"),
):
    """
    Retrieve BOLDetective ranking data for a specimen record.

    Returns ranking information including:
    - **rank**: Quality rank (1-7, where 1 is best)
    - **sumscore**: Sum of all criteria scores (0-15)
    - **criteria**: Individual criterion pass/fail scores

    Returns null if ranking data is not available for the specified processid.
    """
    ranking = get_cb_ranking_by_processid(processid)
    return ranking
