# Scenario 1: Specimen Provenance Lookup - Implementation Plan

## Document Purpose
This document provides a complete technical specification for implementing DiSSCover specimen lookup functionality within the BOLD interface. It is intended for use by a coding agent (Claude Opus 4.5) and contains all details necessary for implementation without additional research.

---

## 1. Overview

### What This Integration Does
When a user views a specimen record in BOLD (e.g., `/record/AAA1234-21`), the system queries DiSSCover to check if a corresponding Digital Specimen exists. If found, BOLD displays a panel showing the DiSSCover DOI, specimen metadata, and direct links to the DiSSCover interface.

### Primary Lookup Strategy: Museum ID via `$filter.physicalSpecimenId`

The **recommended and most reliable** approach for linking BOLD records to DiSSCover specimens is to use the `museumid` field from BCDM (Barcode Core Data Model) with DiSSCover's `$filter.physicalSpecimenId` parameter. This provides an exact match on the physical specimen identifier that both systems share.

**Why Museum ID is the best identifier:**
- The `museumid` in BCDM corresponds directly to the physical specimen's catalog number at the holding institution
- DiSSCover indexes specimens by their `physicalSpecimenId` (e.g., `RMNH.INS.12345`)
- This is the most stable identifier as it refers to the actual physical object, not derived data like Process IDs

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

### BCDM Field: `museumid`
In the Barcode Core Data Model (BCDM), the `museumid` field stores the catalog number or specimen identifier assigned by the holding institution. This is the physical specimen ID that DiSSCover uses as its primary identifier.

**Location in BOLD records**: `records[0].museumid`

**Example values**:
- `RMNH.INS.12345` (Naturalis)
- `ZMB.ARA.67890` (Museum für Naturkunde Berlin)
- `NHMUK.ENT.12345` (Natural History Museum London)

### Files to Create or Modify
| File | Status | Action Required |
|------|--------|-----------------|
| `src/services/dissco.py` | **CREATE** | New service module for DiSSCover API integration |
| `src/views/record.py` | EXISTS | View controller for specimen record pages (no changes needed) |
| `src/templates/record.jinja2` | EXISTS | Template for record pages - **ADD** DiSSCo panel |
| `src/settings.py` | EXISTS | Configuration file - **ADD** DiSSCo settings |
| `src/util.py` | EXISTS | Utility functions including caching (no changes needed) |
| `src/main.py` | EXISTS | FastAPI application - **ADD** DiSSCo route registration |

### Configuration to Add (in `src/settings.py`)

Add the following settings to the `Settings` class:

```python
# DiSSCo Integration Settings
dissco_api_url: str = "https://dev.dissco.tech/api"  # Use dissco.tech/api for production
dissco_api_key: str = ""  # Not needed - API is public
dissco_timeout: int = 30  # Request timeout in seconds
dissco_cache_ttl: int = 3600  # Cache TTL (1 hour)
dissco_enabled: bool = True  # Feature flag for DiSSCo integration
```

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

### Primary Search Method: `$filter.physicalSpecimenId`

**Full URL Example** (using Museum ID):
```
https://dev.dissco.tech/api/digital-specimen/v1/search?$filter.physicalSpecimenId=RMNH.INS.12345&pageSize=10
```

This is the **recommended approach** for BOLD-DiSSCover integration because:
1. It performs an exact match on the physical specimen identifier
2. It directly maps BCDM's `museumid` to DiSSCover's `physicalSpecimenId`
3. It avoids ambiguity from free-text searches

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `$filter.physicalSpecimenId` | string | **PRIMARY** | Exact match on physical specimen ID (use BCDM `museumid`) |
| `q` | string | Fallback | Free-text search query (for cases where museumid is unavailable) |
| `$filter.collectionCode` | string | No | Collection code filter |
| `$filter.species` | string | No | Scientific name filter |
| `pageSize` | integer | No | Results per page (default 25, max 100) |
| `pageNumber` | integer | No | Page number (1-indexed) |

### Search Strategy (Priority Order)

When looking up a BOLD specimen in DiSSCover, use the following priority:

1. **Museum ID (PRIMARY)**: `$filter.physicalSpecimenId={museumid}` 
   - This is the most reliable link as it matches the physical specimen's catalog number
   - Example: `$filter.physicalSpecimenId=RMNH.INS.12345`

2. **Fallback - Free-text search on Museum ID**: `q={museumid}`
   - Use if the exact filter doesn't return results (in case of formatting differences)
   - Example: `q=RMNH.INS.12345`

Note: Process IDs and Sample IDs are BOLD-specific and may not be indexed in DiSSCover. The Museum ID provides the strongest cross-reference to the physical specimen in European collections.

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

### Task 1: Add DiSSCo Settings

**File**: `src/settings.py`

**Action**: Add DiSSCo integration settings to the `Settings` class.

Find the `Settings` class definition and add the following settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # DiSSCo Integration Settings
    dissco_api_url: str = "https://dev.dissco.tech/api"  # Use dissco.tech/api for production
    dissco_api_key: str = ""  # Not needed - API is public
    dissco_timeout: int = 30  # Request timeout in seconds
    dissco_cache_ttl: int = 3600  # Cache TTL (1 hour)
    dissco_enabled: bool = True  # Feature flag for DiSSCo integration
```

---

### Task 2: Create DiSSCover API Service

**File**: `src/services/dissco.py` (**CREATE NEW FILE**)

**Action**: Create a new service module that:

1. Makes HTTP requests to DiSSCover API using `httpx`
2. Uses `$filter.physicalSpecimenId` with the BCDM `museumid` as the **primary** search strategy
3. Falls back to free-text search if exact filter fails
4. Uses Redis caching for responses
5. Handles errors gracefully

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
            return ujson.loads(cached_result[0])
        except:
            pass
    
    # Search Strategy:
    # 1. PRIMARY: Exact match using $filter.physicalSpecimenId
    # 2. FALLBACK: Free-text search in case of formatting differences
    
    search_strategies = [
        # Primary: Exact filter match on physicalSpecimenId
        {"$filter.physicalSpecimenId": museum_id, "pageSize": "10"},
        # Fallback: Free-text search
        {"q": museum_id, "pageSize": "10"},
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
        "message": f"Specimen with Museum ID '{museum_id}' not found in DiSSCo network. The physical specimen may not yet be digitized or registered in a participating European collection."
    }
    
    # Cache negative results with shorter TTL (10 minutes)
    util.write_cache_with_meta_ids(
        {cache_key: ujson.dumps(result)},
        600
    )
    
    return result
```

**Update the API endpoint** to use Museum ID as the primary identifier:

```python
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

### Task 4: Add DiSSCo Panel to Frontend Template

**File**: `src/templates/record.jinja2` (**MODIFY EXISTING FILE**)

**Action**: Add a DiSSCo integration panel to the specimen record page. This requires:
1. Adding JavaScript code to make AJAX calls to the DiSSCo API
2. Adding HTML elements to display the DiSSCo results

**Add the following JavaScript** inside the `$(document).ready()` block (or create one if it doesn't exist):

```javascript
// DiSSCo Integration - Specimen Provenance Lookup (Scenario 1)
// Use museumid as the PRIMARY identifier for DiSSCover lookup
// This maps directly to DiSSCover's $filter.physicalSpecimenId

let museumId = "{{ records[0].museumid|e if records[0].museumid else '' }}";

if (museumId && museumId.trim()) {
    $.ajax({
        url: '/api/dissco/specimen/' + encodeURIComponent(museumId.trim()),
        method: 'GET',
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
                
                // Physical Specimen ID (should match our museumid)
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
                // Show manual search link using museumid
                $('#dissco-manual-search').show();
                $('#dissco-manual-search-link').attr('href', 'https://dev.dissco.tech/search?q=' + encodeURIComponent(museumId));
            }
        },
        error: function(xhr) {
            $('#dissco-status').hide();
            $('#dissco-result').show();
            $('#dissco-found-status').html('<span class="badge badge-warning"><i class="fa fa-exclamation-triangle"></i> Unable to check DiSSCo</span>');
            $('#dissco-manual-search').show();
            $('#dissco-manual-search-link').attr('href', 'https://dev.dissco.tech/search?q=' + encodeURIComponent(museumId));
        }
    });
} else {
    // No Museum ID available - cannot perform lookup
    $('#dissco-status').hide();
    $('#dissco-result').show();
    $('#dissco-found-status').html('<span class="badge badge-secondary">No Museum ID available for DiSSCover lookup</span>');
    $('#dissco-found-status').append('<br><small class="text-muted">A physical specimen identifier (Museum ID) is required to search DiSSCover.</small>');
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

### Task 5: Register DiSSCo Routes in Main Application

**File**: `src/main.py` (**MODIFY EXISTING FILE**)

**Action**: Import the new DiSSCo service and register its routes with the FastAPI application.

**Add import** at the top of the file with other service imports:

```python
from services import (
    # ... existing imports ...
    dissco,
)
```

**Add route registration** in the API router section:

```python
api_router = APIRouter(prefix="/api")
# ... existing route registrations ...
api_router.include_router(dissco.route)
```

This registers the DiSSCo API endpoints under the `/api/dissco` prefix.

---

## 5. Error Handling

### Error Types and Responses

| Error | Cause | BOLD Action |
|-------|-------|-------------|
| No Museum ID | Record doesn't have museumid | Show "No Museum ID available for lookup" |
| Network timeout | DiSSCover slow/unreachable | Show "DiSSCover temporarily unavailable", offer manual search |
| HTTP 4xx | Invalid request | Log error, return not found with message |
| HTTP 5xx | DiSSCover server error | Log error, show "Service unavailable" |
| No results | Specimen not in DiSSCover | Show "Not found" with manual search link |

### Logging

Add appropriate logging calls:
```python
logger.info(f"DiSSCover lookup for museumid: {museum_id}")
logger.warning(f"DiSSCover timeout for museumid: {museum_id}")
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
- [ ] Empty/null museum ID returns appropriate message

### Integration Tests
- [ ] Full lookup flow with real DiSSCover dev API
- [ ] Museum ID exact filter match (`$filter.physicalSpecimenId`) finds specimen
- [ ] Fallback free-text search works when filter fails
- [ ] Non-existent museum ID returns not found
- [ ] Specimen without Museum ID shows appropriate message

### Frontend Tests
- [ ] Panel shows loading state initially
- [ ] Found specimen displays all fields
- [ ] Not found shows message and manual search link
- [ ] No Museum ID shows appropriate message (not error)
- [ ] API error shows warning and manual search link
- [ ] Links to DiSSCover work correctly

### Example Test Cases

| Museum ID | Expected Result |
|-----------|-----------------|
| `RMNH.INS.12345` | Found (if exists in DiSSCover) |
| `ZMB.ARA.67890` | Found (if exists in DiSSCover) |
| `NONEXISTENT.123` | Not found with appropriate message |
| `""` (empty) | "No Museum ID available" message |
| `null` | "No Museum ID available" message |

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

## 9. BCDM to DiSSCover Field Mapping

### Primary Mapping

| BCDM Field | DiSSCover Parameter | DiSSCover Response Field |
|------------|---------------------|--------------------------|
| `museumid` | `$filter.physicalSpecimenId` | `ods:physicalSpecimenID` |

### Field Mapping Table

| BCDM Field | Type | DiSSCover Equivalent | Notes |
|------------|------|---------------------|-------|
| `museumid` | string | `ods:physicalSpecimenID` | **PRIMARY KEY** - catalog number / specimen ID |
| `inst` | string | `ods:organisationCode` | Institution code |
| `species` | string | `ods:specimenName` | May differ due to taxonomic updates |
| `country/ocean` | string | - | Available via `dwc:country` in full response |

### Why Museum ID is the Best Identifier

1. **Stability**: Museum IDs are permanent identifiers assigned by institutions
2. **Uniqueness**: Catalog numbers are unique within each institution
3. **Cross-system compatibility**: Both BOLD and DiSSCover use the same physical specimen ID
4. **No transformation needed**: The `museumid` value can be used directly in the DiSSCover filter

---

## 10. Summary of Changes

| File | Action | Description |
|------|--------|-------------|
| `src/settings.py` | **Modify** | Add DiSSCo settings (`dissco_api_url`, `dissco_enabled`, etc.) |
| `src/services/dissco.py` | **Create** | New service module with DiSSCover API client |
| `src/templates/record.jinja2` | **Modify** | Add DiSSCo integration panel with JavaScript |
| `src/main.py` | **Modify** | Register DiSSCo API routes |

### New API Endpoint

```
GET /api/dissco/specimen/{museum_id}
```

This endpoint accepts a Museum ID (BCDM `museumid` field) and queries DiSSCover using `$filter.physicalSpecimenId`.

### Dependencies

No new dependencies required. Uses existing BOLD infrastructure:
- `httpx` (already used in BOLD for HTTP requests)
- `ujson` (already used in BOLD for JSON serialization)
- Redis caching via `util.py` (already used in BOLD)

---

## 11. Rollout Plan

1. **Development**: Implement against `https://dev.dissco.tech/api`
2. **Testing**: Test with known BOLD specimens that have Museum IDs registered in DiSSCover
3. **Staging**: Deploy to staging environment, verify caching and error handling
4. **Production**: Switch `dissco_api_url` to `https://dissco.tech/api`

The feature flag `dissco_enabled` allows quick rollback if issues arise.

---

## 12. Example API Calls

### Looking up a specimen by Museum ID

**Request:**
```
GET https://dev.dissco.tech/api/digital-specimen/v1/search?$filter.physicalSpecimenId=RMNH.INS.12345&pageSize=10
```

**Expected Response (if found):**
```json
{
  "data": [
    {
      "id": "20.5000.1025/ABC-123-XYZ",
      "type": "digitalSpecimen",
      "attributes": {
        "@id": "https://doi.org/20.5000.1025/ABC-123-XYZ",
        "ods:physicalSpecimenID": "RMNH.INS.12345",
        "ods:specimenName": "Apis mellifera",
        "ods:organisationName": "Naturalis Biodiversity Center",
        "ods:organisationCode": "RMNH",
        "ods:midsLevel": 2,
        "ods:isKnownToContainMedia": true
      }
    }
  ],
  "meta": {
    "totalRecords": 1
  }
}
```

### BOLD Internal API Call

**Request:**
```
GET /api/dissco/specimen/RMNH.INS.12345
```

**Expected Response:**
```json
{
  "found": true,
  "dissco_id": "https://doi.org/20.5000.1025/ABC-123-XYZ",
  "physical_specimen_id": "RMNH.INS.12345",
  "institution": {
    "name": "Naturalis Biodiversity Center",
    "code": "RMNH",
    "country": ""
  },
  "specimen_name": "Apis mellifera",
  "mids_level": 2,
  "has_media": true,
  "specimen_url": "https://dev.dissco.tech/ds/20.5000.1025/ABC-123-XYZ",
  "last_sync": "2025-01-15T10:30:00.000Z"
}
```
