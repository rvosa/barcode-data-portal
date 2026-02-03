# Major Enhancements in the `develop` Branch

This document describes the major enhancements that have been added to the `develop` branch in comparison with the `main` branch. These enhancements integrate BOLD more deeply into the wider landscape of biodiversity research infrastructures and improve contributions to DNA barcode reference library development.

---

## Overview

The `develop` branch introduces two significant categories of new functionality:

1. **DiSSCo Integration** - Linking BOLD specimen records to the Distributed System of Scientific Collections (DiSSCo), enabling discovery of physical specimens in European natural science collections.

2. **BOLDetective Ranking System** - Exposing automated quality rankings of BOLD records through both the API and web interface, supporting the development of high-quality DNA barcode reference libraries.

---

## User Perspective

### DiSSCo Integration: Connecting Digital and Physical Specimens

#### What is DiSSCo?

[DiSSCo](https://www.dissco.eu/) (Distributed System of Scientific Collections) is a European research infrastructure providing unified digital access to natural science collections across Europe. It enables researchers to discover and access information about physical specimens held in European museums, herbaria, and other natural history institutions.

#### How does the integration benefit users?

When viewing a specimen record in BOLD, users can now see whether a corresponding physical specimen exists in the DiSSCo network. This integration provides:

- **Specimen Provenance Discovery**: Automatically checks if the physical voucher specimen is registered in a participating European collection.
- **Direct Links to DiSSCover**: When a match is found, users can navigate directly to the specimen's page in DiSSCover to access additional metadata, images, and institutional information.
- **Data Quality Indicators**: Shows the MIDS (Minimum Information about a Digital Specimen) completeness level, helping users assess data quality.
- **Institution Information**: Displays which institution holds the physical specimen and provides linkage to collection metadata.
- **Media Availability**: Indicates whether additional images or media are available in DiSSCover.

#### What do users see?

On each specimen record page, a new "DiSSCo Digital Specimen" panel appears that:

1. Shows the lookup status (searching, found, or not found)
2. Displays the DiSSCo DOI identifier when available
3. Provides a direct link to view the specimen in DiSSCover
4. Shows institutional and taxonomic information from DiSSCo
5. Offers a manual search option if automatic matching fails

This integration allows researchers to seamlessly bridge the gap between molecular data in BOLD and physical specimen data in European collections, enabling more comprehensive biodiversity research.

---

### BOLDetective Ranking System: Quality Assessment for Reference Libraries

#### What is BOLDetective?

BOLDetective is a quality assessment system that evaluates BOLD records against 15 standardized criteria to determine their suitability for inclusion in DNA barcode reference libraries. Each record receives a rank from 1 (highest quality) to 7 (needs improvement).

#### Why is this important for reference libraries?

DNA barcode reference libraries are foundational tools for species identification. High-quality reference libraries require:

- Accurate taxonomic identifications
- Complete specimen metadata
- Quality sequence data
- Proper vouchering

The BOLDetective ranking system helps curators and researchers:

- **Prioritize records** for inclusion in curated reference libraries
- **Identify data gaps** that could be filled with additional specimen information
- **Ensure quality standards** are met for taxonomic and ecological research
- **Track improvements** to data quality over time

#### Evaluation Criteria

Records are evaluated against these 15 criteria:

| Criterion | Description |
|-----------|-------------|
| Species-level ID | Has a valid species-level taxonomic identification |
| BIN Assigned | Has been assigned to a Barcode Index Number |
| Sequence Quality | Sequence is ≥500 base pairs in length |
| Type Specimen | Specimen has type status (holotype, paratype, etc.) |
| Has Image | Specimen image is available |
| Named Identifier | Identified by a named taxonomist (not automated) |
| Morphological ID Method | Identification includes morphological assessment |
| Country/Ocean Present | Geographic country or ocean is recorded |
| Coordinates Present | GPS coordinates are available |
| Collection Date Present | Date of collection is recorded |
| Collector Present | Collector name is recorded |
| Locality Present | Specific locality information is available |
| Public Institution | Specimen is held at a public institution |
| Museum ID Present | Museum/catalog ID is recorded |
| Voucher Status | Proper voucher specimen exists |

#### Ranking Scale

| Rank | Description |
|------|-------------|
| 1 | Highest quality - meets all or nearly all criteria |
| 2 | Excellent - minor gaps in metadata |
| 3 | Very good - most criteria satisfied |
| 4 | Good - suitable for many applications |
| 5 | Moderate - some significant gaps |
| 6 | Limited - substantial improvements needed |
| 7 | Minimal - significant data gaps present |

#### Where can users access rankings?

- **Web Interface**: Each specimen record page now includes a "Record Quality (BOLDetective)" section showing the rank, total score, and individual criterion evaluations.
- **API Endpoint**: Rankings can be retrieved programmatically via the `/api/ranking/{processid}` endpoint.

---

## Technological Solutions

### DiSSCo Integration: Technical Implementation

#### API Service (`src/services/dissco.py`)

The DiSSCo integration is implemented as a new FastAPI service module with the following components:

**Configuration Settings** (`src/settings.py`):
```python
dissco_api_url: str = "https://disscover.dissco.eu/api"
dissco_timeout: int = 30
dissco_cache_ttl: int = 3600
dissco_enabled: bool = True
```

**API Endpoint**:
- `GET /api/dissco/specimen/{museum_id}` - Looks up a specimen in DiSSCover by museum ID

**Key Technical Features**:

1. **Asynchronous HTTP Client**: Uses `httpx` for non-blocking HTTP requests to the DiSSCover API.

2. **Caching Strategy**: Results are cached using the existing Redis/file system caching infrastructure:
   - Successful lookups are cached for 1 hour (configurable)
   - Negative results (not found) are cached for 10 minutes to reduce API load

3. **Free-text Search with Validation**: Since DiSSCover's `physicalSpecimenId` filter requires the full namespaced URL, the integration uses a free-text search (`q` parameter) and validates that the museum ID appears in the returned `ods:physicalSpecimenID` field.

4. **Pydantic Response Models**: Ensures type-safe API responses with proper documentation.

**Response Structure**:
```json
{
  "found": true,
  "dissco_id": "https://doi.org/10.xxxx/yyyy",
  "physical_specimen_id": "RMNH.INS.12345",
  "institution": {
    "name": "Naturalis Biodiversity Center",
    "code": "RMNH",
    "country": null
  },
  "specimen_name": "Genus species",
  "mids_level": 2,
  "has_media": true,
  "specimen_url": "https://dissco.tech/ds/10.xxxx/yyyy",
  "last_sync": "2024-01-15T12:00:00Z",
  "message": null
}
```

#### Web Interface (`src/templates/includes/disscover_panel.jinja2`)

The frontend component is implemented as a Jinja2 template include that:

1. Extracts the `museumid` from the current BCDM record
2. Makes an AJAX request to the DiSSCo API endpoint
3. Dynamically updates the UI based on the response
4. Provides graceful degradation when lookups fail or data is unavailable

---

### BOLDetective Ranking System: Technical Implementation

#### ETL Pipeline (`src/ETL/extract_rank_summary.py`)

The ranking extraction script processes BCDM JSON-L records and evaluates each against the 15 criteria:

**Processing Pipeline**:
```
BCDM.jsonl → extract_rank_summary.py → specimen_ranks.jsonl → Couchbase (specimen_ranks collection)
```

**Criteria Evaluation Logic**:

Each criterion is evaluated using a dedicated function that returns `1` (pass) or `0` (fail):

```python
def evaluate_species_level_id(record: Dict[str, Any]) -> int:
    """Check for valid species-level identification."""
    species = record.get("species", "")
    id_rank = record.get("identification_rank", "")
    
    # Valid ranks are defined as species-level or below per BCDM taxonomy model
    if not species or id_rank not in ("species", "subspecies"):
        return 0
    
    # Check for invalid patterns (sp., cf., aff., etc.)
    if INVALID_SPECIES_PATTERNS.search(species):
        return 0
    
    return 1
```

**Rank Assignment**:

The final rank (1-7) is determined by hierarchical criteria satisfaction based on the sum score and specific criteria combinations.

#### Database Storage

Rankings are stored in a dedicated Couchbase collection:

```sql
CREATE COLLECTION `DERIVED`.`_default`.`specimen_ranks`;
```

**Document Structure**:
```json
{
  "processid": "AACTA2950-20",
  "rank": 4,
  "sumscore": 11,
  "criteria": {
    "species_level_id": 1,
    "bin_assigned": 1,
    "sequence_quality": 1,
    "type_status": 0,
    "has_image": 1,
    "identifier_named": 1,
    "id_method_morphological": 1,
    "country_present": 1,
    "coords_present": 0,
    "collection_date_present": 1,
    "collector_present": 1,
    "locality_present": 1,
    "institution_public": 1,
    "museum_id_present": 0,
    "voucher_status": 1
  }
}
```

#### API Service (`src/services/ranking.py`)

**API Endpoint**:
- `GET /api/ranking/{processid}` - Retrieves ranking data for a specimen record

**Query Implementation**:
```python
def get_cb_ranking_by_processid(processid: str) -> Optional[Dict]:
    """Retrieve ranking data from the specimen_ranks collection."""
    bucket = dao.NAME_MAP["specimen_ranks"]["bucket"]
    collection = dao.NAME_MAP["specimen_ranks"]["collection"]
    
    # Obtain cluster connection from the application's connection pool (dao module)
    cluster = dao._get_cb_cluster()
    
    query = f"""
        SELECT `{collection}`.*
        FROM `{bucket}`.`_default`.`{collection}`
        WHERE processid = $processid
    """
    
    result = cluster.query(query, processid=processid)
    rows = list(result.rows())
    return rows[0] if rows else None
```

#### Web Interface (`src/templates/record.jinja2`)

The specimen record page includes a new "Record Quality (BOLDetective)" section that:

1. Displays the overall rank and score
2. Shows a table of all 15 criteria with pass/fail indicators
3. Uses server-side rendering with Jinja2 for optimal performance
4. Gracefully handles records without ranking data

**View Controller** (`src/views/record.py`):

The record view fetches ranking data alongside other specimen information:

```python
# Fetch ranking data for this record
ranking_data = None
try:
    resp = await client.get(
        url=f"{get_app_url()}/api/ranking/{processid}",
    )
    if resp.status_code == 200:
        ranking_data = resp.json()
except (httpx.HTTPError, httpx.TimeoutException):
    # Ranking data is optional, so we ignore network/timeout errors
    pass
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        BCDM Records                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              extract_rank_summary.py (ETL)                       │
│  • Evaluate 15 BOLDetective criteria                            │
│  • Calculate rank (1-7) and sum score                           │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Couchbase (specimen_ranks collection)               │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
┌──────────────────────────┐      ┌──────────────────────────────┐
│    API: /api/ranking/    │      │     Web: /record/{id}        │
│    Returns JSON          │      │     Shows ranking panel      │
└──────────────────────────┘      └──────────────────────────────┘
                                             │
                                             ▼
                               ┌──────────────────────────────┐
                               │  DiSSCo Panel (museumid)     │
                               │  AJAX → /api/dissco/specimen │
                               │       → DiSSCover API        │
                               └──────────────────────────────┘
```

---

## Additional Technical Improvements

The `develop` branch also includes several supporting enhancements:

1. **Retry Logic for Couchbase Operations**: Transient timeout errors are handled with automatic retries, improving reliability under load.

2. **Environment Configuration**: Settings can now be configured via environment variables, supporting containerized deployments.

3. **GitLab CI/CD Pipeline**: A comprehensive CI/CD configuration has been added for automated testing and deployment.

4. **Ansible Deployment Playbooks**: Infrastructure-as-code support for production deployments.

5. **Enhanced Documentation**: README files have been added throughout the codebase explaining each component's purpose and usage.

---

## Conclusion

These enhancements position BOLD as a more integrated participant in the global biodiversity informatics landscape. The DiSSCo integration bridges molecular and physical specimen data across European collections, while the BOLDetective ranking system provides transparent quality metrics that support the curation of high-quality DNA barcode reference libraries. Both features are accessible through the web interface for interactive use and via the API for programmatic integration with external tools and pipelines.
