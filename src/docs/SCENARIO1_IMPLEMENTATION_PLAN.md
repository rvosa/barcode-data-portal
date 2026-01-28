# Scenario 1: Specimen Provenance Lookup - Implementation Plan

## Document Purpose
This document provides a complete technical specification for implementing DiSSCover specimen lookup functionality within the BOLD interface. It is intended for use by a coding agent (Claude Opus 4.5) and contains all details necessary for implementation without additional research.

---

## 1. Overview

### What This Integration Does
When a user views a specimen record in BOLD (e.g., `/record/AAA1234-21`), the system queries DiSSCover to check if a corresponding Digital Specimen exists. If found, BOLD displays a panel showing the DiSSCover DOI, specimen metadata, and direct links to the DiSSCover interface.

### Architecture: Backend Proxy Pattern

```
┌──────────────────┐                    ┌──────────────────┐                    ┌──────────────────┐
│                  │    AJAX Request    │                  │    HTTPS GET       │                  │
│   BOLD Frontend  │ ─────────────────► │   BOLD Backend   │ ─────────────────► │  DiSSCover API   │
│   (JavaScript)   │                    │   (FastAPI)      │                    │  (REST/JSON)     │
│                  │ ◄───────────────── │                  │ ◄───────────────── │                  │
│                  │    JSON Response   │                  │    JSON Response   │                  │
└──────────────────┘                    └──────────────────┘                    └──────────────────┘
```

### Key Principles
- **No authentication required**: DiSSCover's search API is public and read-only
- **No CORS issues**: BOLD backend acts as proxy, avoiding browser CORS restrictions
- **Caching**: Responses cached in Redis for 1 hour (configurable via `dissco_cache_ttl`)
- **Graceful degradation**: Frontend handles API errors gracefully

---

## 2. BOLD Codebase Context

### Technology Stack (Authoritative)
- **Backend Framework**: FastAPI (Python 3.x)
- **Frontend**: Jinja2 templates with jQuery for AJAX
- **Caching**: Redis (existing infrastructure in BOLD)
- **HTTP Client**: `httpx` (async) for internal calls; should use `httpx` for external DiSSCover calls
- **Configuration**: Pydantic Settings via `src/settings.py`

### Relevant Existing Files
| File | Purpose |
|------|---------|
| `src/services/dissco.py` | **EXISTS** - Currently has mock implementation, needs real API calls |
| `src/views/record.py` | View controller for specimen record pages |
| `src/templates/record.jinja2` | **EXISTS** - Template with DiSSCo panel, needs refinement |
| `src/settings.py` | **EXISTS** - Has DiSSCo settings, needs URL update |
| `src/util.py` | Utility functions including caching |

### Existing Configuration (in `src/settings.py`)
```python
# DiSSCo Integration Settings - CURRENTLY SET TO:
dissco_api_url: str = "https://disscover.disco.eu/api/v1"  # NEEDS UPDATE
dissco_api_key: str = ""  # Not needed - API is public
dissco_timeout: int = 30  # OK
dissco_cache_ttl: int = 3600  # OK (1 hour)
dissco_enabled: bool = True  # Feature flag - OK
```

**CORRECTION NEEDED**: The `dissco_api_url` should be updated to `https://dev.dissco.tech/api` for development or `https://dissco.tech/api` for production.

---

## 3. DiSSCover API Specification

### Base URLs

| Environment | Base URL |
|-------------|----------|
| Production  | `https://dissco.tech/api` |
| Development | `https://dev.dissco.tech/api` |
| Sandbox     | `https://sandbox.dissco.tech/api` |

**Recommendation**: Use `https://dev.dissco.tech/api` for initial implementation.

### Search Endpoint

```
GET /digital-specimen/v1/search
```

**Full URL Example**:
```
https://dev.dissco.tech/api/digital-specimen/v1/search?q=BOLD:AAA1234-21&pageSize=10
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | No | Free-text search query |
| `$filter.physicalSpecimenId` | string | No | Exact match on physical specimen ID |
| `$filter.collectionCode` | string | No | Collection code filter |
| `$filter.species` | string | No | Scientific name filter |
| `pageSize` | integer | No | Results per page (default 25, max 100) |
| `pageNumber` | integer | No | Page number (1-indexed) |

### Search Strategy for BOLD Identifiers

BOLD can query DiSSCover using multiple identifier types. Try these in order:

1. **BOLD Process ID with prefix**: `q=BOLD:{processid}` (e.g., `q=BOLD:AAA1234-21`)
2. **BOLD Process ID raw**: `q={processid}` (e.g., `q=AAA1234-21`)
3. **Sample ID**: `q={sampleid}`
4. **Museum ID / Catalog Number**: `$filter.physicalSpecimenId={museumid}`

### API Response Format

**Successful Response (HTTP 200)**:
```json
{
  "data": [
    {
      "id": "20.5000.1025/ABC-123-XYZ",
      "type": "digitalSpecimen",
      "attributes": {
        "@id": "https://doi.org/20.5000.1025/ABC-123-XYZ",
        "@type": "ods:DigitalSpecimen",
        "dcterms:identifier": "https://doi.org/20.5000.1025/ABC-123-XYZ",
        "ods:version": 3,
        "ods:status": "Active",
        "dcterms:modified": "2025-01-15T10:30:00.000Z",
        "ods:midsLevel": 2,
        "ods:physicalSpecimenID": "RMNH.INS.12345",
        "ods:specimenName": "Apis mellifera",
        "ods:organisationID": "https://ror.org/0566bfb96",
        "ods:organisationName": "Naturalis Biodiversity Center",
        "ods:organisationCode": "RMNH",
        "dwc:collectionCode": "INS",
        "ods:isKnownToContainMedia": true,
        "dcterms:license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "ods:hasIdentifications": [
          {
            "@type": "ods:Identification",
            "ods:hasTaxonIdentifications": [
              {
                "@type": "ods:TaxonIdentification",
                "dwc:scientificName": "Apis mellifera Linnaeus, 1758",
                "dwc:genus": "Apis",
                "dwc:family": "Apidae"
              }
            ]
          }
        ]
      }
    }
  ],
  "links": {
    "self": "https://dev.dissco.tech/api/digital-specimen/v1/search?q=RMNH.INS.12345"
  },
  "meta": {
    "totalRecords": 1
  }
}
```

**No Results (HTTP 200)**:
```json
{
  "data": [],
  "links": { "self": "..." },
  "meta": { "totalRecords": 0 }
}
```

### Key Response Fields to Extract

| Field Path | Description | Use in BOLD |
|------------|-------------|-------------|
| `data[0].attributes.@id` | Full DOI URL | Link to DiSSCover page |
| `data[0].attributes.dcterms:identifier` | DOI identifier | Display as identifier |
| `data[0].attributes.ods:midsLevel` | Data completeness (0-3) | Progress indicator |
| `data[0].attributes.ods:specimenName` | Primary specimen name | Confirmation display |
| `data[0].attributes.ods:organisationName` | Institution name | Attribution |
| `data[0].attributes.ods:organisationCode` | Institution code | Short reference |
| `data[0].attributes.ods:physicalSpecimenID` | Physical specimen ID | Cross-reference |
| `data[0].attributes.ods:isKnownToContainMedia` | Has images/media | Media indicator |

### MIDS Level Interpretation

| Level | Meaning | Description |
|-------|---------|-------------|
| 0 | Minimal | Just the identifier |
| 1 | Basic | + scientific name, institution |
| 2 | Extended | + collection event, geography |
| 3 | Full | + images, sequences, all metadata |

---

## 4. Implementation Tasks

### Task 1: Update Settings

**File**: `src/settings.py`

**Change**: Update `dissco_api_url` default value:
```python
# FROM:
dissco_api_url: str = "https://disscover.disco.eu/api/v1"

# TO:
dissco_api_url: str = "https://dev.dissco.tech/api"
```

**Note**: The `dissco_api_key` setting can remain empty as the API is public.

---

### Task 2: Implement Real DiSSCover API Client

**File**: `src/services/dissco.py`

**Replace the mock `_mock_dissco_specimen_lookup` function** with a real implementation that:

1. Makes HTTP requests to DiSSCover API using `httpx`
2. Implements the search strategy (try multiple identifier formats)
3. Uses Redis caching for responses
4. Handles errors gracefully

**Implementation**:

```python
import httpx
from typing import Dict, Any, Optional
import hashlib
import ujson

# Add these imports at top of file
try:
    import util
    from settings import settings
except ImportError:
    import sys
    import pathlib
    sys.path.append(pathlib.Path(__file__).parent.parent.resolve().as_posix())
    import util
    from settings import settings

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


def _generate_cache_key(identifier: str, identifier_type: str) -> str:
    """Generate a cache key for DiSSCover lookups."""
    key_string = f"dissco:specimen:{identifier_type}:{identifier}"
    return hashlib.md5(key_string.encode()).hexdigest()


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
    # Format: https://dev.dissco.tech/ds/{DOI}
    specimen_url = f"https://dev.dissco.tech/ds/{doi_suffix}"
    
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
    identifier: str,
    identifier_type: str = "processid"
) -> Dict[str, Any]:
    """
    Look up a specimen in DiSSCover using multiple search strategies.
    
    Args:
        identifier: The specimen identifier (process ID, sample ID, or museum ID)
        identifier_type: Type of identifier ('processid', 'sampleid', 'museumid')
        
    Returns:
        Dict with lookup results
    """
    dissco_settings = _get_dissco_settings()
    cache_ttl = dissco_settings["cache_ttl"]
    
    # Check cache first
    cache_key = _generate_cache_key(identifier, identifier_type)
    cached_result = util.get_cache_from_meta_ids([cache_key])
    if cached_result and cached_result[0]:
        try:
            return ujson.loads(cached_result[0])
        except:
            pass
    
    # Build search strategies based on identifier type
    search_strategies = []
    
    if identifier_type == "processid":
        # Try with BOLD: prefix first, then raw
        search_strategies = [
            {"q": f"BOLD:{identifier}", "pageSize": "5"},
            {"q": identifier, "pageSize": "5"},
        ]
    elif identifier_type == "sampleid":
        search_strategies = [
            {"q": identifier, "pageSize": "5"},
        ]
    elif identifier_type == "museumid":
        # Use structured filter for museum IDs
        search_strategies = [
            {"$filter.physicalSpecimenId": identifier, "pageSize": "5"},
            {"q": identifier, "pageSize": "5"},
        ]
    else:
        search_strategies = [
            {"q": identifier, "pageSize": "5"},
        ]
    
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
            
            return result
    
    # No results from any strategy
    result = {
        "found": False,
        "message": "Specimen not found in DiSSCo network. The physical specimen may not yet be digitized or registered in a participating European collection."
    }
    
    # Cache negative results with shorter TTL (10 minutes)
    util.write_cache_with_meta_ids(
        {cache_key: ujson.dumps(result)},
        600
    )
    
    return result
```

**Update the API endpoint** to use the new async function:

```python
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
        default="processid",
        title="Identifier Type",
        description="Type of identifier being provided",
        pattern="(sampleid|processid|museumid)",
    ),
):
    """Look up a single specimen in the DiSSCo network."""
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    # Perform real lookup
    result = await lookup_specimen_in_disscover(identifier, identifier_type)

    return DiSSCoSpecimenResponse(**result)
```

---

### Task 3: Update Response Model

**File**: `src/services/dissco.py`

**Update `DiSSCoSpecimenResponse`** to include new fields from DiSSCover:

```python
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
```

---

### Task 4: Update Frontend Template

**File**: `src/templates/record.jinja2`

**Update the JavaScript** to handle new response fields and improve display:

```javascript
// DiSSCo Integration - Specimen Provenance Lookup (Scenario 1)
// Try processid first (most reliable for BOLD records)
let processId = "{{ processid|e }}";
let sampleId = "{{ records[0].sampleid|e if records[0].sampleid else '' }}";
let museumId = "{{ records[0].museumid|e if records[0].museumid else '' }}";

// Determine best identifier to use
let lookupId = processId || sampleId;
let lookupType = processId ? 'processid' : 'sampleid';

if (lookupId) {
    $.ajax({
        url: '/api/dissco/specimen/' + encodeURIComponent(lookupId),
        method: 'GET',
        data: { identifier_type: lookupType },
        success: function(response) {
            $('#dissco-status').hide();
            $('#dissco-result').show();
            
            if (response.found) {
                $('#dissco-found-status').html('<span class="badge badge-success"><i class="fa fa-check"></i> Found in DiSSCo</span>');
                
                // DOI
                if (response.dissco_id) {
                    $('#dissco-id-row').show();
                    let doiDisplay = response.dissco_id.replace('https://doi.org/', '');
                    $('#dissco-id').html('<a href="' + response.specimen_url + '" target="_blank" class="navy-link">' + doiDisplay + ' <i class="fa fa-external-link"></i></a>');
                }
                
                // Institution
                if (response.institution) {
                    $('#dissco-institution-row').show();
                    let instText = response.institution.name;
                    if (response.institution.code) {
                        instText += ' (' + response.institution.code + ')';
                    }
                    $('#dissco-institution').text(instText);
                }
                
                // Physical Specimen ID
                if (response.physical_specimen_id) {
                    $('#dissco-specimen-row').show();
                    $('#dissco-specimen-id').text(response.physical_specimen_id);
                }
                
                // Specimen Name
                if (response.specimen_name) {
                    $('#dissco-name-row').show();
                    $('#dissco-name').html('<em>' + response.specimen_name + '</em>');
                }
                
                // MIDS Level
                if (response.mids_level !== null && response.mids_level !== undefined) {
                    $('#dissco-mids-row').show();
                    let midsPercent = (response.mids_level / 3) * 100;
                    $('#dissco-mids').html(
                        '<div class="progress" style="height: 20px; margin-bottom: 0;">' +
                        '<div class="progress-bar" role="progressbar" style="width: ' + midsPercent + '%" ' +
                        'aria-valuenow="' + response.mids_level + '" aria-valuemin="0" aria-valuemax="3">' +
                        'Level ' + response.mids_level + '/3</div></div>'
                    );
                }
                
                // Media indicator
                if (response.has_media) {
                    $('#dissco-media-row').show();
                    $('#dissco-media').html('<i class="fa fa-camera"></i> Media available in DiSSCover');
                }
                
                // View button
                if (response.specimen_url) {
                    $('#dissco-link-row').show();
                    $('#dissco-link').attr('href', response.specimen_url);
                }
            } else {
                $('#dissco-found-status').html('<span class="badge badge-secondary"><i class="fa fa-info-circle"></i> Not found in DiSSCo network</span>');
                if (response.message) {
                    $('#dissco-found-status').append('<br><small class="text-muted">' + response.message + '</small>');
                }
                // Show manual search link
                $('#dissco-manual-search').show();
                $('#dissco-manual-search-link').attr('href', 'https://dev.dissco.tech/search?q=' + encodeURIComponent(lookupId));
            }
        },
        error: function(xhr) {
            $('#dissco-status').hide();
            $('#dissco-result').show();
            $('#dissco-found-status').html('<span class="badge badge-warning"><i class="fa fa-exclamation-triangle"></i> Unable to check DiSSCo</span>');
            $('#dissco-manual-search').show();
            $('#dissco-manual-search-link').attr('href', 'https://dev.dissco.tech/search?q=' + encodeURIComponent(lookupId));
        }
    });
} else {
    $('#dissco-status').hide();
    $('#dissco-result').show();
    $('#dissco-found-status').html('<span class="badge badge-secondary">No identifier available for lookup</span>');
}
```

**Update the HTML panel** in the template:

```html
<div class="ibox">
    <div class="ibox-content">
        <div class="navy-line"></div>
        <h1><i class="fa fa-globe"></i> DiSSCo Digital Specimen</h1>
        <div id="dissco-status">
            <div class="sk-spinner sk-spinner-wave">
                <div class="sk-rect1"></div>
                <div class="sk-rect2"></div>
                <div class="sk-rect3"></div>
                <div class="sk-rect4"></div>
                <div class="sk-rect5"></div>
            </div>
            <p class="text-muted">Checking DiSSCover network...</p>
        </div>
        <div id="dissco-result" style="display: none;">
            <table class="table table-striped">
                <tr>
                    <th>Status:</th>
                    <td id="dissco-found-status"></td>
                </tr>
                <tr id="dissco-id-row" style="display: none;">
                    <th>DOI:</th>
                    <td id="dissco-id"></td>
                </tr>
                <tr id="dissco-institution-row" style="display: none;">
                    <th>Holding Institution:</th>
                    <td id="dissco-institution"></td>
                </tr>
                <tr id="dissco-specimen-row" style="display: none;">
                    <th>Physical Specimen ID:</th>
                    <td id="dissco-specimen-id"></td>
                </tr>
                <tr id="dissco-name-row" style="display: none;">
                    <th>Specimen Name:</th>
                    <td id="dissco-name"></td>
                </tr>
                <tr id="dissco-mids-row" style="display: none;">
                    <th>Data Completeness:</th>
                    <td id="dissco-mids"></td>
                </tr>
                <tr id="dissco-media-row" style="display: none;">
                    <th>Media:</th>
                    <td id="dissco-media"></td>
                </tr>
                <tr id="dissco-link-row" style="display: none;">
                    <th>View in DiSSCover:</th>
                    <td><a id="dissco-link" href="#" target="_blank" class="btn btn-sm btn-primary"><i class="fa fa-external-link"></i> Open in DiSSCover</a></td>
                </tr>
            </table>
            <div id="dissco-manual-search" style="display: none;" class="text-center">
                <a id="dissco-manual-search-link" href="#" target="_blank" class="btn btn-sm btn-default">
                    <i class="fa fa-search"></i> Search DiSSCover manually
                </a>
            </div>
        </div>
        <p class="text-muted small">
            <a href="https://www.dissco.eu/" target="_blank">DiSSCo</a> (Distributed System of Scientific Collections) 
            provides unified digital access to European natural science collections.
        </p>
    </div>
</div>
```

---

### Task 5: Add Convenience Endpoint for Process ID Lookup

**File**: `src/services/dissco.py`

Add a convenience endpoint that tries multiple search strategies automatically:

```python
@route.get(
    "/lookup/{process_id}",
    response_model=DiSSCoSpecimenResponse,
    response_description="DiSSCo Lookup by BOLD Process ID",
)
async def lookup_by_process_id(
    process_id: str = Path(
        ...,
        title="BOLD Process ID",
        description="BOLD Process ID (e.g., AAA1234-21)",
    ),
):
    """
    Convenience endpoint to look up a specimen by BOLD Process ID.
    
    This endpoint automatically tries multiple search strategies:
    1. Search with BOLD: prefix
    2. Search with raw process ID
    
    Use this endpoint when you have a BOLD Process ID and want the
    system to automatically find the best match.
    """
    dissco_settings = _get_dissco_settings()

    if not dissco_settings["enabled"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DiSSCo integration is currently disabled",
        )

    result = await lookup_specimen_in_disscover(process_id, "processid")
    return DiSSCoSpecimenResponse(**result)
```

---

## 5. Error Handling

### Error Types and Responses

| Error | Cause | BOLD Action |
|-------|-------|-------------|
| Network timeout | DiSSCover slow/unreachable | Show "DiSSCover temporarily unavailable", offer manual search |
| HTTP 4xx | Invalid request | Log error, return not found with message |
| HTTP 5xx | DiSSCover server error | Log error, show "Service unavailable" |
| No results | Specimen not in DiSSCover | Show "Not found" with manual search link |

### Logging

Add appropriate logging calls:
```python
logger.info(f"DiSSCover lookup: {identifier_type}:{identifier}")
logger.warning(f"DiSSCover timeout for {identifier}")
logger.error(f"DiSSCover API error: {error}")
```

---

## 6. Testing Checklist

### Unit Tests
- [ ] `_query_disscover` handles timeout correctly
- [ ] `_query_disscover` handles HTTP errors correctly
- [ ] `_parse_disscover_response` extracts all fields correctly
- [ ] `_parse_disscover_response` handles empty response
- [ ] Cache key generation is consistent
- [ ] Caching stores and retrieves correctly

### Integration Tests
- [ ] Full lookup flow with real DiSSCover dev API
- [ ] Process ID with BOLD: prefix finds specimen
- [ ] Raw process ID finds specimen
- [ ] Sample ID lookup works
- [ ] Museum ID lookup works
- [ ] Non-existent specimen returns not found

### Frontend Tests
- [ ] Panel shows loading state initially
- [ ] Found specimen displays all fields
- [ ] Not found shows message and manual search link
- [ ] API error shows warning and manual search link
- [ ] Links to DiSSCover work correctly

---

## 7. Configuration Summary

### Environment Variables

These can be set via environment variables (Pydantic Settings will pick them up):

```bash
# For development
export DISSCO_API_URL="https://dev.dissco.tech/api"
export DISSCO_ENABLED="true"
export DISSCO_TIMEOUT="30"
export DISSCO_CACHE_TTL="3600"

# For production
export DISSCO_API_URL="https://dissco.tech/api"
```

### Feature Flag

The `dissco_enabled` setting provides a feature flag to disable the integration without code changes:

```python
# In settings.py - can be controlled via environment
dissco_enabled: bool = True  # Set to False to disable
```

When disabled:
- API endpoints return 503 Service Unavailable
- Frontend should hide or grey out the DiSSCo panel

---

## 8. Links to DiSSCover

### Specimen Detail Page
```
https://dev.dissco.tech/ds/{DOI}
```
Example: `https://dev.dissco.tech/ds/20.5000.1025/ABC-123-XYZ`

### Manual Search Page
```
https://dev.dissco.tech/search?q={QUERY}
```
Example: `https://dev.dissco.tech/search?q=AAA1234-21`

---

## 9. Summary of Changes

| File | Action | Description |
|------|--------|-------------|
| `src/settings.py` | Modify | Update `dissco_api_url` default to `https://dev.dissco.tech/api` |
| `src/services/dissco.py` | Modify | Replace mock with real API client, add caching, update response model |
| `src/templates/record.jinja2` | Modify | Update JS and HTML for enhanced display |

### Dependencies

No new dependencies required. Uses existing:
- `httpx` (already used in BOLD)
- `ujson` (already used in BOLD)
- Redis caching via `util.py` (already used in BOLD)

---

## 10. Rollout Plan

1. **Development**: Implement against `https://dev.dissco.tech/api`
2. **Testing**: Test with known BOLD specimens that exist in DiSSCover
3. **Staging**: Deploy to staging environment, verify caching and error handling
4. **Production**: Switch `dissco_api_url` to `https://dissco.tech/api`

The feature flag `dissco_enabled` allows quick rollback if issues arise.
