"""
DiSSCo Integration Service

This module provides API endpoints for integrating BOLD with DiSSCo 
(Distributed System of Scientific Collections) via the disscover.disco.eu API.

The integration supports three main scenarios:
1. Specimen Provenance Lookup - Find physical specimens in DiSSCo network
2. Batch Sample Tracking - Track multiple specimens across European collections
3. Synchronization Status - Monitor data sync between BOLD and DiSSCo

For detailed documentation, see: docs/DISSCO_INTEGRATION.md
"""

from fastapi import APIRouter, Path, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import pathlib
import sys
import uuid

try:
    import util
    from settings import settings
except ImportError:
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import util
    from settings import settings

route = APIRouter(prefix="/dissco", tags=["dissco"])

logger = logging.getLogger("dissco_logger")


# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================


class DiSSCoInstitution(BaseModel):
    """Institution information from DiSSCo."""

    name: str = Field(..., description="Institution name")
    code: str = Field(..., description="Institution code")
    country: str = Field(..., description="Country where institution is located")


class DiSSCoSpecimenResponse(BaseModel):
    """Response model for single specimen lookup."""

    found: bool = Field(..., description="Whether specimen was found in DiSSCo")
    dissco_id: Optional[str] = Field(
        None, description="DiSSCo persistent identifier (Handle)"
    )
    physical_specimen_id: Optional[str] = Field(
        None, description="Physical specimen identifier"
    )
    institution: Optional[DiSSCoInstitution] = Field(
        None, description="Holding institution information"
    )
    specimen_status: Optional[str] = Field(None, description="Specimen preservation status")
    last_sync: Optional[str] = Field(
        None, description="Last synchronization timestamp (ISO 8601)"
    )
    specimen_url: Optional[str] = Field(
        None, description="Direct URL to specimen in DiSSCo"
    )
    message: Optional[str] = Field(None, description="Additional information or error message")


class TrackingRequest(BaseModel):
    """Request model for batch sample tracking."""

    query_id: Optional[str] = Field(None, description="BOLD query ID for specimen set")
    identifiers: List[str] = Field(
        ..., description="List of specimen identifiers to track"
    )
    identifier_type: str = Field(
        default="sampleid",
        description="Type of identifier (sampleid, processid, museumid)",
    )
    fields_requested: List[str] = Field(
        default=["institution", "specimen_status", "last_modified"],
        description="Fields to include in tracking response",
    )


class TrackingResult(BaseModel):
    """Single specimen tracking result."""

    bold_identifier: str = Field(..., description="Original BOLD identifier")
    dissco_status: str = Field(
        ..., description="Status: found, not_found, or pending"
    )
    dissco_id: Optional[str] = Field(None, description="DiSSCo identifier if found")
    institution: Optional[str] = Field(None, description="Holding institution name")
    suggestion: Optional[str] = Field(None, description="Suggestion for unmatched specimens")


class TrackingResponse(BaseModel):
    """Response model for batch tracking request."""

    tracking_id: str = Field(..., description="Unique tracking request identifier")
    total_requested: int = Field(..., description="Total specimens requested")
    matched: int = Field(..., description="Number of specimens found in DiSSCo")
    unmatched: int = Field(..., description="Number of specimens not found")
    results: List[TrackingResult] = Field(..., description="Individual tracking results")
    institutions_summary: Dict[str, int] = Field(
        ..., description="Summary of specimens by institution"
    )


class SyncDiscrepancy(BaseModel):
    """Data discrepancy between BOLD and DiSSCo."""

    taxonomy_mismatch: int = Field(default=0, description="Records with taxonomy differences")
    location_mismatch: int = Field(default=0, description="Records with location differences")
    date_mismatch: int = Field(default=0, description="Records with date differences")


class SyncEvent(BaseModel):
    """Recent synchronization event."""

    timestamp: str = Field(..., description="Event timestamp (ISO 8601)")
    event_type: str = Field(..., description="Type of sync event")
    count: int = Field(..., description="Number of records affected")
    description: str = Field(..., description="Human-readable event description")


class SyncSummary(BaseModel):
    """Synchronization summary statistics."""

    total_bold_records: int = Field(..., description="Total records in BOLD")
    matched_in_dissco: int = Field(..., description="Records matched in DiSSCo")
    pending_match: int = Field(..., description="Records pending matching")
    not_in_dissco: int = Field(..., description="Records not in DiSSCo network")
    last_sync_time: Optional[str] = Field(None, description="Last sync timestamp")
    next_scheduled_sync: Optional[str] = Field(None, description="Next scheduled sync")


class SyncStatusResponse(BaseModel):
    """Response model for institution sync status."""

    institution_code: str = Field(..., description="Institution code")
    institution_name: str = Field(..., description="Institution name")
    sync_summary: SyncSummary = Field(..., description="Sync statistics")
    discrepancies: SyncDiscrepancy = Field(..., description="Data discrepancies found")
    recent_events: List[SyncEvent] = Field(..., description="Recent sync events")


class HealthResponse(BaseModel):
    """Health check response for DiSSCo integration."""

    status: str = Field(..., description="Integration status: healthy, degraded, or unavailable")
    dissco_api_reachable: bool = Field(..., description="Whether DiSSCo API is reachable")
    last_successful_request: Optional[str] = Field(
        None, description="Last successful API call timestamp"
    )
    message: Optional[str] = Field(None, description="Additional status information")


# =============================================================================
# Helper Functions
# =============================================================================


def _get_dissco_settings() -> Dict[str, Any]:
    """Get DiSSCo configuration settings."""
    return {
        "api_url": getattr(settings, "dissco_api_url", "https://disscover.disco.eu/api/v1"),
        "timeout": getattr(settings, "dissco_timeout", 30),
        "enabled": getattr(settings, "dissco_enabled", True),
        "cache_ttl": getattr(settings, "dissco_cache_ttl", 3600),
    }


def _generate_tracking_id() -> str:
    """Generate a unique tracking ID for batch requests."""
    timestamp = datetime.utcnow().strftime("%Y")
    unique_id = uuid.uuid4().hex[:8].upper()
    return f"TRK-{timestamp}-{unique_id}"


def _mock_dissco_specimen_lookup(identifier: str, identifier_type: str) -> Dict[str, Any]:
    """
    Mock DiSSCo specimen lookup for demonstration.
    
    In production, this would make actual HTTP requests to the DiSSCo API:
    https://disscover.disco.eu/api/v1/specimens/search?q={identifier}
    
    The DiSSCo API provides:
    - Specimen search by various identifiers
    - Full specimen metadata including institution details
    - Persistent Handle identifiers for specimens
    """
    # Simulate a found specimen for demonstration purposes
    # Real implementation would use httpx to call DiSSCo API
    demo_specimens = {
        "SAMPLE001": {
            "found": True,
            "dissco_id": "https://hdl.handle.net/20.5000.1025/XYZ-789-ABC",
            "physical_specimen_id": "RMNH.INS.123456",
            "institution": {
                "name": "Naturalis Biodiversity Center",
                "code": "RMNH",
                "country": "Netherlands",
            },
            "specimen_status": "preserved",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "specimen_url": "https://disscover.disco.eu/specimen/XYZ-789-ABC",
        },
        "SAMPLE002": {
            "found": True,
            "dissco_id": "https://hdl.handle.net/20.5000.1025/MFN-456-DEF",
            "physical_specimen_id": "ZMB.ARA.12345",
            "institution": {
                "name": "Museum für Naturkunde Berlin",
                "code": "MFN",
                "country": "Germany",
            },
            "specimen_status": "preserved",
            "last_sync": datetime.utcnow().isoformat() + "Z",
            "specimen_url": "https://disscover.disco.eu/specimen/MFN-456-DEF",
        },
    }

    if identifier.upper() in demo_specimens:
        return demo_specimens[identifier.upper()]

    return {
        "found": False,
        "message": "Specimen not found in DiSSCo network. The physical specimen may not yet be digitized or registered in a participating European collection.",
    }


def _mock_dissco_batch_lookup(identifiers: List[str], identifier_type: str) -> List[Dict[str, Any]]:
    """
    Mock batch lookup for multiple specimens.
    
    In production, this would batch requests to DiSSCo API or use their
    bulk search endpoint if available.
    """
    results = []
    for identifier in identifiers:
        result = _mock_dissco_specimen_lookup(identifier, identifier_type)
        result["bold_identifier"] = identifier
        results.append(result)
    return results


def _mock_institution_sync_status(institution_code: str) -> Dict[str, Any]:
    """
    Mock institution synchronization status.
    
    In production, this would:
    1. Query BOLD database for institution record count
    2. Query DiSSCo API for matched specimens from this institution
    3. Compare and identify discrepancies
    4. Retrieve recent sync events from a tracking database
    """
    # Demo data for demonstration purposes
    demo_institutions = {
        "CBG": {
            "institution_name": "Centre for Biodiversity Genomics",
            "sync_summary": {
                "total_bold_records": 125000,
                "matched_in_dissco": 45000,
                "pending_match": 5000,
                "not_in_dissco": 75000,
                "last_sync_time": "2026-01-28T12:00:00Z",
                "next_scheduled_sync": "2026-01-29T00:00:00Z",
            },
            "discrepancies": {
                "taxonomy_mismatch": 234,
                "location_mismatch": 56,
                "date_mismatch": 12,
            },
            "recent_events": [
                {
                    "timestamp": "2026-01-28T11:45:00Z",
                    "event_type": "new_match",
                    "count": 150,
                    "description": "150 new specimens matched with DiSSCo records",
                },
                {
                    "timestamp": "2026-01-27T18:30:00Z",
                    "event_type": "discrepancy_resolved",
                    "count": 25,
                    "description": "25 taxonomy discrepancies resolved via DiSSCo update",
                },
            ],
        },
        "RMNH": {
            "institution_name": "Naturalis Biodiversity Center",
            "sync_summary": {
                "total_bold_records": 85000,
                "matched_in_dissco": 72000,
                "pending_match": 3000,
                "not_in_dissco": 10000,
                "last_sync_time": "2026-01-28T10:00:00Z",
                "next_scheduled_sync": "2026-01-29T00:00:00Z",
            },
            "discrepancies": {
                "taxonomy_mismatch": 89,
                "location_mismatch": 23,
                "date_mismatch": 5,
            },
            "recent_events": [
                {
                    "timestamp": "2026-01-28T09:30:00Z",
                    "event_type": "full_sync",
                    "count": 72000,
                    "description": "Completed full synchronization with DiSSCo",
                },
            ],
        },
    }

    if institution_code.upper() in demo_institutions:
        return demo_institutions[institution_code.upper()]

    # Return default empty status for unknown institutions
    return {
        "institution_name": f"Institution {institution_code}",
        "sync_summary": {
            "total_bold_records": 0,
            "matched_in_dissco": 0,
            "pending_match": 0,
            "not_in_dissco": 0,
            "last_sync_time": None,
            "next_scheduled_sync": None,
        },
        "discrepancies": {
            "taxonomy_mismatch": 0,
            "location_mismatch": 0,
            "date_mismatch": 0,
        },
        "recent_events": [],
    }


# =============================================================================
# API Endpoints
# =============================================================================


@route.get(
    "/health",
    response_model=HealthResponse,
    response_description="DiSSCo Integration Health Status",
)
async def check_dissco_health():
    """
    Check the health status of the DiSSCo integration.
    
    Returns the current status of the connection to DiSSCo's API and 
    information about recent successful requests.
    
    This endpoint can be used by monitoring systems to verify that
    the BOLD-DiSSCo integration is functioning correctly.
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        return HealthResponse(
            status="disabled",
            dissco_api_reachable=False,
            message="DiSSCo integration is currently disabled in configuration",
        )

    # In production, this would actually test the DiSSCo API connection
    # For now, return a healthy status for demonstration
    return HealthResponse(
        status="healthy",
        dissco_api_reachable=True,
        last_successful_request=datetime.utcnow().isoformat() + "Z",
        message=f"DiSSCo API endpoint: {dissco_settings['api_url']}",
    )


@route.get(
    "/specimen/{identifier}",
    response_model=DiSSCoSpecimenResponse,
    response_description="DiSSCo Specimen Lookup Result",
)
async def lookup_specimen_in_dissco(
    identifier: str = Path(
        ...,
        title="Specimen Identifier",
        description="Sample ID, Process ID, or Museum ID to search for",
    ),
    identifier_type: str = Query(
        default="sampleid",
        title="Identifier Type",
        description="Type of identifier being provided",
        pattern="(sampleid|processid|museumid)",
    ),
):
    """
    Look up a single specimen in the DiSSCo network.
    
    **Scenario 1: Specimen Provenance Lookup**
    
    This endpoint searches the DiSSCo (Distributed System of Scientific Collections) 
    network for a physical specimen matching the provided identifier. If found, 
    it returns information about:
    
    - The DiSSCo persistent identifier (Handle)
    - The holding institution and its location
    - The preservation status of the specimen
    - A direct link to view the specimen in DiSSCo's disscover portal
    
    This enables users viewing a DNA barcode record on BOLD to discover if the 
    source specimen exists in a European natural science collection and access
    additional provenance information.
    
    **Parameters:**
    - **identifier**: The specimen identifier to search for (Sample ID, Process ID, or Museum ID)
    - **identifier_type**: The type of identifier (sampleid, processid, museumid)
    
    **Example Request:**
    ```
    GET /api/dissco/specimen/SAMPLE001?identifier_type=sampleid
    ```
    
    **Integration with DiSSCo API:**
    This endpoint queries the DiSSCo specimen registry at disscover.disco.eu 
    to find matching physical specimens. The matching is performed using 
    standard specimen identifiers that link DNA barcoding records to 
    physical voucher specimens.
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    # Perform lookup (mock for demonstration, real impl would call DiSSCo API)
    result = _mock_dissco_specimen_lookup(identifier, identifier_type)

    return DiSSCoSpecimenResponse(**result)


@route.post(
    "/track",
    response_model=TrackingResponse,
    response_description="Batch Sample Tracking Result",
)
async def track_samples_in_dissco(request: TrackingRequest):
    """
    Track multiple specimens in the DiSSCo network.
    
    **Scenario 2: Batch Sample Tracking Export**
    
    This endpoint allows researchers to submit a batch of specimen identifiers
    to be tracked across the DiSSCo network. It returns a summary of:
    
    - How many specimens were found in DiSSCo
    - Which institutions hold the physical specimens
    - Detailed results for each specimen
    - A tracking ID for future reference
    
    This supports workflows where researchers need to trace the provenance of
    DNA samples back to physical specimens housed in European collections.
    
    **Use Cases:**
    - A researcher querying specimens on BOLD wants to know which ones have
      registered physical vouchers in European museums
    - An institution wants to verify that their donated specimens are properly
      registered in the DiSSCo network
    - A biodiversity project needs to track specimen usage across institutions
    
    **Request Body:**
    - **query_id**: Optional BOLD query ID to link this tracking request
    - **identifiers**: List of specimen identifiers to track
    - **identifier_type**: Type of identifiers (sampleid, processid, museumid)
    - **fields_requested**: Which fields to include in results
    
    **Example Request:**
    ```json
    {
        "identifiers": ["SAMPLE001", "SAMPLE002", "SAMPLE003"],
        "identifier_type": "sampleid",
        "fields_requested": ["institution", "specimen_status"]
    }
    ```
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    if not request.identifiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one identifier must be provided",
        )

    # Perform batch lookup
    raw_results = _mock_dissco_batch_lookup(request.identifiers, request.identifier_type)

    # Process results
    results = []
    institutions_summary: Dict[str, int] = {}
    matched_count = 0

    for raw_result in raw_results:
        if raw_result.get("found"):
            matched_count += 1
            institution_name = raw_result.get("institution", {}).get("name", "Unknown")
            institutions_summary[institution_name] = (
                institutions_summary.get(institution_name, 0) + 1
            )

            results.append(
                TrackingResult(
                    bold_identifier=raw_result["bold_identifier"],
                    dissco_status="found",
                    dissco_id=raw_result.get("dissco_id"),
                    institution=institution_name,
                )
            )
        else:
            results.append(
                TrackingResult(
                    bold_identifier=raw_result["bold_identifier"],
                    dissco_status="not_found",
                    suggestion="Specimen may not yet be digitized in DiSSCo network",
                )
            )

    return TrackingResponse(
        tracking_id=_generate_tracking_id(),
        total_requested=len(request.identifiers),
        matched=matched_count,
        unmatched=len(request.identifiers) - matched_count,
        results=results,
        institutions_summary=institutions_summary,
    )


@route.get(
    "/sync/status/{institution_code}",
    response_model=SyncStatusResponse,
    response_description="Institution Synchronization Status",
)
async def get_institution_sync_status(
    institution_code: str = Path(
        ...,
        title="Institution Code",
        description="Code identifying the institution (e.g., CBG, RMNH)",
    ),
):
    """
    Get synchronization status between BOLD and DiSSCo for an institution.
    
    **Scenario 3: Data Synchronization Status Dashboard**
    
    This endpoint provides institution administrators with a comprehensive
    view of the synchronization status between their BOLD records and 
    corresponding entries in the DiSSCo network.
    
    The response includes:
    
    - **Sync Summary**: Counts of matched, pending, and unmatched records
    - **Discrepancies**: Identified differences between BOLD and DiSSCo data
    - **Recent Events**: Timeline of recent synchronization activities
    
    This supports data quality workflows where institutions need to:
    - Monitor the coverage of their specimens in DiSSCo
    - Identify and resolve data inconsistencies
    - Track synchronization progress over time
    
    **Parameters:**
    - **institution_code**: The institutional code (e.g., CBG, RMNH, MFN)
    
    **Example Request:**
    ```
    GET /api/dissco/sync/status/CBG
    ```
    
    **Data Discrepancies:**
    The discrepancies section identifies records where BOLD and DiSSCo data
    don't match:
    - **taxonomy_mismatch**: Different species identification
    - **location_mismatch**: Different collection locality
    - **date_mismatch**: Different collection dates
    
    Institution administrators can use this information to investigate
    and resolve inconsistencies in their data.
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    # Get sync status (mock for demonstration)
    status_data = _mock_institution_sync_status(institution_code)

    return SyncStatusResponse(
        institution_code=institution_code.upper(),
        institution_name=status_data["institution_name"],
        sync_summary=SyncSummary(**status_data["sync_summary"]),
        discrepancies=SyncDiscrepancy(**status_data["discrepancies"]),
        recent_events=[SyncEvent(**event) for event in status_data["recent_events"]],
    )
