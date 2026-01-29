from fastapi import APIRouter, Path, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

import hashlib
import httpx
import logging
import pathlib
import sys
import ujson

# Standard BOLD import pattern
try:
    import util
    from settings import settings
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import util
    from settings import settings

# Initialize logger
logger = logging.getLogger(__name__)

route = APIRouter(tags=["dissco"], prefix="/dissco")


# Helper Functions


def _get_dissco_settings():
    """Get DiSSCo settings from application configuration."""
    return {
        "api_url": settings.dissco_api_url,
        "enabled": settings.dissco_enabled,
        "timeout": settings.dissco_timeout,
        "cache_ttl": settings.dissco_cache_ttl,
    }


def _generate_cache_key(identifier: str, identifier_type: str) -> str:
    """Generate a cache key for DiSSCover lookups."""
    key_string = f"dissco:specimen:{identifier_type}:{identifier}"
    return hashlib.md5(key_string.encode()).hexdigest()


async def _query_disscover(query_params: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Make a request to DiSSCover API.

    Args:
        query_params: Dictionary of query parameters

    Returns:
        API response as dict, or None on error
    """
    dissco_settings = _get_dissco_settings()
    base_url = dissco_settings["api_url"]
    timeout = dissco_settings["timeout"]

    url = f"{base_url}/digital-specimen/v1/search"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                params=query_params,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.warning(f"DiSSCover API timeout for params: {query_params}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"DiSSCover API HTTP error {e.response.status_code}: {e}")
        return None
    except Exception as e:
        logger.error(f"DiSSCover API error: {e}")
        return None


def _parse_disscover_response(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse DiSSCover API response into BOLD's response format.

    Args:
        api_response: Raw DiSSCover API response

    Returns:
        Formatted response for BOLD frontend
    """
    if not api_response or not api_response.get("data"):
        return {
            "found": False,
            "message": "Specimen not found in DiSSCo network. The physical specimen may not yet be digitized or registered in a participating European collection."
        }

    # Take the first (best) match
    specimen = api_response["data"][0]["attributes"]

    # Extract DOI - remove URL prefix if present
    doi = specimen.get("dcterms:identifier", "")
    doi_suffix = doi.replace("https://doi.org/", "")

    # Build specimen URL for DiSSCover
    # Format: https://dissco.tech/ds/{DOI}
    specimen_url = f"https://dissco.tech/ds/{doi_suffix}"

    # Extract institution info
    institution = None
    if specimen.get("ods:organisationName"):
        institution = {
            "name": specimen.get("ods:organisationName", ""),
            "code": specimen.get("ods:organisationCode", ""),
            "country": ""  # Not directly available, would need ROR lookup
        }

    # Extract taxonomy for display
    specimen_name = specimen.get("ods:specimenName", "")

    return {
        "found": True,
        "dissco_id": doi,
        "physical_specimen_id": specimen.get("ods:physicalSpecimenID"),
        "institution": institution,
        "specimen_name": specimen_name,
        "mids_level": specimen.get("ods:midsLevel"),
        "has_media": specimen.get("ods:isKnownToContainMedia", False),
        "specimen_url": specimen_url,
        "last_sync": specimen.get("dcterms:modified"),
    }


async def lookup_specimen_in_disscover(
    museum_id: str
) -> Dict[str, Any]:
    """
    Look up a specimen in DiSSCover using the Museum ID (physicalSpecimenId).

    This is the PRIMARY search method for BOLD-DiSSCover integration.
    The museumid from BCDM maps directly to DiSSCover's physicalSpecimenId field.

    Args:
        museum_id: The Museum ID / catalog number from BCDM (records[0].museumid)

    Returns:
        Dict with lookup results
    """
    if not museum_id or not museum_id.strip():
        return {
            "found": False,
            "message": "No Museum ID available for this specimen. DiSSCover lookup requires a physical specimen identifier."
        }

    museum_id = museum_id.strip()

    dissco_settings = _get_dissco_settings()
    cache_ttl = dissco_settings["cache_ttl"]

    # Check cache first
    cache_key = _generate_cache_key(museum_id, "museumid")
    cached_result = util.get_cache_from_meta_ids([cache_key])
    if cached_result and cached_result[0]:
        try:
            logger.info(f"DiSSCover cache hit for museumid: {museum_id}")
            return ujson.loads(cached_result[0])
        except:
            pass

    # Search Strategy:
    # 1. PRIMARY: Exact match using $filter.physicalSpecimenId
    # 2. FALLBACK: Free-text search in case of formatting differences

    search_strategies = [
        # Primary: Exact filter match on physicalSpecimenId
        {"physicalSpecimenId": museum_id, "pageSize": "10"},
        # Fallback: Free-text search
        {"q": museum_id, "pageSize": "10"},
    ]

    logger.info(f"DiSSCover lookup for museumid: {museum_id}")

    # Try each strategy until we get results
    for params in search_strategies:
        api_response = await _query_disscover(params)

        if api_response and api_response.get("data"):
            result = _parse_disscover_response(api_response)

            # Cache successful results
            util.write_cache_with_meta_ids(
                {cache_key: ujson.dumps(result)},
                cache_ttl
            )

            logger.info(f"DiSSCover specimen found for museumid: {museum_id}")
            return result

    # No results from any strategy
    result = {
        "found": False,
        "message": f"Specimen with Museum ID '{museum_id}' not found in DiSSCo network. The physical specimen may not yet be digitized or registered in a participating European collection."
    }

    # Cache negative results with shorter TTL (10 minutes)
    util.write_cache_with_meta_ids(
        {cache_key: ujson.dumps(result)},
        600
    )

    logger.info(f"DiSSCover specimen not found for museumid: {museum_id}")
    return result


# Pydantic Models


class DiSSCoInstitution(BaseModel):
    """Institution information from DiSSCover."""

    name: str = Field(..., description="Institution name")
    code: Optional[str] = Field(None, description="Institution code")
    country: Optional[str] = Field(None, description="Institution country")


class DiSSCoSpecimenResponse(BaseModel):
    """Response model for single specimen lookup."""

    found: bool = Field(..., description="Whether specimen was found in DiSSCo")
    dissco_id: Optional[str] = Field(
        None, description="DiSSCo DOI identifier"
    )
    physical_specimen_id: Optional[str] = Field(
        None, description="Physical specimen identifier"
    )
    institution: Optional[DiSSCoInstitution] = Field(
        None, description="Holding institution information"
    )
    specimen_name: Optional[str] = Field(
        None, description="Scientific name from DiSSCover"
    )
    mids_level: Optional[int] = Field(
        None, description="MIDS data completeness level (0-3)"
    )
    has_media: Optional[bool] = Field(
        None, description="Whether specimen has associated media"
    )
    specimen_url: Optional[str] = Field(
        None, description="Direct URL to specimen in DiSSCover"
    )
    last_sync: Optional[str] = Field(
        None, description="Last modification timestamp (ISO 8601)"
    )
    message: Optional[str] = Field(
        None, description="Additional information or error message"
    )


# API Endpoints


@route.get(
    "/specimen/{museum_id}",
    response_model=DiSSCoSpecimenResponse,
    response_description="DiSSCo Specimen Lookup Result",
)
async def lookup_specimen_in_dissco(
    museum_id: str = Path(
        ...,
        title="Museum ID",
        description="Physical specimen identifier (BCDM museumid field, e.g., RMNH.INS.12345)",
    ),
):
    """
    Look up a single specimen in the DiSSCo network by Museum ID.

    **Primary Lookup Method**

    This endpoint searches DiSSCover using the `$filter.physicalSpecimenId` parameter,
    which maps directly to the BCDM `museumid` field. This provides the most reliable
    link between BOLD records and DiSSCover Digital Specimens.

    **Parameters:**
    - **museum_id**: The Museum ID / catalog number from the BCDM (e.g., RMNH.INS.12345)

    **Example Request:**
    ```
    GET /api/dissco/specimen/RMNH.INS.12345
    ```

    **Returns:**
    - DiSSCo specimen information if found
    - Not found message if specimen is not in DiSSCo network
    - Error message if DiSSCo service is unavailable
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    # Perform lookup using Museum ID (physicalSpecimenId)
    result = await lookup_specimen_in_disscover(museum_id)

    return DiSSCoSpecimenResponse(**result)