# DiSSCo Integration Scenarios for BOLD

This document describes three scenarios for enhancing the BOLD (Barcode of Life Data) portal 
to interact with DiSSCo (Distributed System of Scientific Collections) via the 
disscover.disco.eu API, specifically focusing on "Sample Data Brokering and Tracking" 
data services.

## Overview

[DiSSCo](https://www.dissco.eu/) is the European Research Infrastructure for natural science 
collections, providing unified digital access to specimen data across European institutions. 
The integration between BOLD (boldsystems.org) and DiSSCo's disscover platform enables:

- Cross-referencing of specimen data between DNA barcoding and physical collections
- Enhanced sample provenance tracking
- Bidirectional data synchronization for shared specimens
- Enriched metadata discovery through federated searches

## Scenario 1: Specimen Provenance Lookup

### User Story
A user viewing a specimen record on boldsystems.org can see if the same specimen exists in 
DiSSCo's network of European natural science collections, providing additional provenance 
information and links to the physical specimen in the holding institution.

### User Experience Flow
1. User navigates to a record page on boldsystems.org (e.g., `/record/PROCESSID123`)
2. The page displays specimen information including taxonomy, collection data, and sequences
3. A new "DiSSCo Integration" panel shows:
   - Status indicator showing if the specimen is registered in DiSSCo
   - Link to the corresponding DiSSCo specimen page (if found)
   - Physical specimen location in the European collection network
   - Last synchronization timestamp

### Technical Implementation
- **API Endpoint**: `GET /api/dissco/specimen/{sample_id}`
- **DiSSCo Query**: Searches DiSSCo's specimen registry by sample ID, museum ID, or catalog number
- **Response**: Includes DiSSCo specimen identifiers, collection information, and direct links

### Example API Response
```json
{
  "found": true,
  "dissco_id": "https://hdl.handle.net/20.5000.1025/ABC-123-DEF",
  "physical_specimen_id": "RMNH.INS.123456",
  "institution": {
    "name": "Naturalis Biodiversity Center",
    "code": "RMNH",
    "country": "Netherlands"
  },
  "specimen_status": "preserved",
  "last_sync": "2026-01-15T10:30:00Z",
  "specimen_url": "https://disscover.disco.eu/specimen/ABC-123-DEF"
}
```

---

## Scenario 2: Batch Sample Tracking Export

### User Story
A researcher who has queried a set of specimens on BOLD can export tracking information to 
monitor these samples across the DiSSCo network. This supports workflows where DNA samples 
were extracted from physical specimens housed in European collections.

### User Experience Flow
1. User performs a search query on BOLD (e.g., by taxonomy, geography, or institution)
2. Results page shows matching specimens with sequence data
3. User clicks "Track in DiSSCo" button
4. System generates a tracking request containing:
   - List of sample identifiers (Sample IDs, Museum IDs, Process IDs)
   - Metadata fields requested for tracking
   - User's notification preferences
5. User receives a tracking summary showing:
   - How many samples were found in DiSSCo
   - Institutions holding the physical specimens
   - Options to subscribe to updates for these specimens

### Technical Implementation
- **API Endpoint**: `POST /api/dissco/track`
- **Request Body**: Query ID and list of sample identifiers
- **DiSSCo Integration**: Bulk lookup against DiSSCo's specimen registry
- **Response**: Tracking summary with matched and unmatched specimens

### Example API Request
```json
{
  "query_id": "abc123query",
  "identifiers": ["SAMPLE001", "SAMPLE002", "SAMPLE003"],
  "identifier_type": "sampleid",
  "fields_requested": ["institution", "specimen_status", "last_modified"]
}
```

### Example API Response
```json
{
  "tracking_id": "TRK-2026-00001",
  "total_requested": 3,
  "matched": 2,
  "unmatched": 1,
  "results": [
    {
      "bold_sampleid": "SAMPLE001",
      "dissco_status": "found",
      "dissco_id": "https://hdl.handle.net/20.5000.1025/XYZ-789",
      "institution": "Museum für Naturkunde Berlin"
    },
    {
      "bold_sampleid": "SAMPLE002", 
      "dissco_status": "found",
      "dissco_id": "https://hdl.handle.net/20.5000.1025/ABC-456",
      "institution": "Natural History Museum London"
    },
    {
      "bold_sampleid": "SAMPLE003",
      "dissco_status": "not_found",
      "suggestion": "Specimen may not yet be digitized in DiSSCo network"
    }
  ],
  "institutions_summary": {
    "Museum für Naturkunde Berlin": 1,
    "Natural History Museum London": 1
  }
}
```

---

## Scenario 3: Data Synchronization Status Dashboard

### User Story
Institution administrators can view a dashboard showing the synchronization status between 
their BOLD records and corresponding DiSSCo entries. This supports data quality workflows 
and ensures consistency between DNA barcode data and physical specimen records.

### User Experience Flow
1. User navigates to their institution dashboard on BOLD (e.g., `/inst/INSTITUTION_CODE`)
2. A new "DiSSCo Sync Status" tab shows:
   - Total specimens from this institution in BOLD
   - Specimens matched with DiSSCo records
   - Specimens with data discrepancies (e.g., taxonomy mismatches)
   - Recent synchronization events
3. User can:
   - View detailed discrepancy reports
   - Request re-synchronization for specific records
   - Export synchronization status reports

### Technical Implementation
- **API Endpoint**: `GET /api/dissco/sync/status/{institution_code}`
- **Dashboard View**: New template showing synchronization metrics
- **DiSSCo Integration**: Periodic polling of DiSSCo's data broker API for institution records
- **Caching**: Sync status cached with configurable TTL for performance

### Example API Response
```json
{
  "institution_code": "CBG",
  "institution_name": "Centre for Biodiversity Genomics",
  "sync_summary": {
    "total_bold_records": 125000,
    "matched_in_dissco": 45000,
    "pending_match": 5000,
    "not_in_dissco": 75000,
    "last_sync_time": "2026-01-28T12:00:00Z",
    "next_scheduled_sync": "2026-01-29T00:00:00Z"
  },
  "discrepancies": {
    "taxonomy_mismatch": 234,
    "location_mismatch": 56,
    "date_mismatch": 12
  },
  "recent_events": [
    {
      "timestamp": "2026-01-28T11:45:00Z",
      "event_type": "new_match",
      "count": 150,
      "description": "150 new specimens matched with DiSSCo records"
    },
    {
      "timestamp": "2026-01-27T18:30:00Z", 
      "event_type": "discrepancy_resolved",
      "count": 25,
      "description": "25 taxonomy discrepancies resolved via DiSSCo update"
    }
  ]
}
```

---

## Configuration

The DiSSCo integration requires the following configuration in `settings.py`:

```python
# DiSSCo Integration Settings
dissco_api_url: str = "https://disscover.disco.eu/api/v1"
dissco_api_key: str = ""  # API key for authenticated requests
dissco_timeout: int = 30  # Request timeout in seconds
dissco_cache_ttl: int = 3600  # Cache TTL for DiSSCo responses (1 hour)
dissco_enabled: bool = True  # Feature flag for DiSSCo integration
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dissco/specimen/{identifier}` | GET | Look up single specimen in DiSSCo |
| `/api/dissco/track` | POST | Submit batch tracking request |
| `/api/dissco/sync/status/{institution}` | GET | Get institution sync status |
| `/api/dissco/health` | GET | Check DiSSCo API connectivity |

## Security Considerations

1. **API Key Protection**: DiSSCo API keys stored as environment variables, never in code
2. **Rate Limiting**: Respect DiSSCo API rate limits; implement request queuing if needed
3. **Data Privacy**: Only share specimen identifiers, not sensitive collection data
4. **Timeout Handling**: Graceful degradation when DiSSCo API is unavailable

## Future Enhancements

- Bidirectional data updates (push corrections back to DiSSCo)
- Real-time webhook notifications for specimen updates
- Integration with DiSSCo's annotation services
- Support for DiSSCo's Digital Specimen identifiers (DOIs)
