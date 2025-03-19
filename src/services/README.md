# Services

This directory contains the API service implementations for the BOLD Public Portal. These services form the backbone of both the REST API and the web interface by providing data access, processing, and manipulation capabilities.

## Overview

The services layer sits between the web views and the data access layer. It handles:

1. Processing API requests
2. Interacting with the Data Access Object (DAO) layer
3. Transforming and preparing data for consumption
4. Implementing business logic
5. Caching results for performance optimization

Each service is implemented as a FastAPI router with defined endpoints, input validation, and response models.

## Service Modules

- **ancillary.py**: Retrieves metadata and reference information from ancillary collections
- **counts.py**: Generates metadata count statistics for queries
- **develop.py**: Development endpoints for data manipulation (not included in schema)
- **documents.py**: Retrieves and formats document data, handles downloads in various formats
- **images.py**: Retrieves and processes image metadata and URLs
- **maps.py**: Generates geographic maps based on coordinate data
- **qr.py**: Generates QR codes for sequences and records
- **query.py**: Handles the main search functionality, storing results in cache
- **query_parse.py**: Parses free-text queries into structured triplet format
- **query_preprocessor.py**: Resolves and expands query terms to match database entries
- **stats.py**: Provides general statistics about the database
- **summary.py**: Generates metadata summaries by aggregating fields from documents
- **taxonomy.py**: Retrieves and processes taxonomic data, hierarchies, and maps
- **terms.py**: Handles term lookup and autocompletion functionality
- **test.py**: Simple test endpoints for service validation

## Key Concepts

### Triplet Query Format

Many services work with a "triplet" query format:
```
scope:subscope:value
```

For example:
- `tax:species:Homo sapiens` (Taxonomy scope, species rank, value "Homo sapiens")
- `geo:country:Canada` (Geography scope, country subscope, value "Canada")
- `bin:uri:BOLD:AAA1234` (BIN scope, URI subscope, value "BOLD:AAA1234")

This format allows for precise and structured data querying.

### Caching Mechanism

The services implement a multi-level caching strategy:
- Redis for in-memory caching of frequently accessed data
- File-based caching for larger result sets
- Query IDs that encode the original query for cache lookup

### Response Models

Most services use Pydantic models to validate and structure response data, ensuring consistent API behavior.

## Integration with Overall Architecture

The services layer:

1. **Consumes from**:
   - FastAPI routing system
   - DAO layer (`dao.py`) for database access
   - Utility functions (`util.py`) for caching and query processing

2. **Produces for**:
   - API consumers (direct REST API access)
   - Web views layer (through internal API calls)

3. **Flow of data**:
   - Request comes in via FastAPI route
   - Service processes the request, validates parameters
   - Service calls DAO methods to retrieve data
   - Service transforms data into the appropriate response format
   - Response is sent back to the caller (API client or view)

## Security and Performance

- Services implement query validation to prevent injection attacks
- Large queries are paginated to prevent excessive resource usage
- Caching is used extensively to reduce database load
- Complex operations are optimized for performance

## Error Handling

Services implement consistent error handling patterns:
- HTTP status codes for different error conditions
- Detailed error messages for debugging
- Custom exception handling where appropriate

## Related Components

- **dao.py**: Data Access Object that services use to interact with the database
- **util.py**: Utility functions for caching, query processing, and security
- **views/**: Web view controllers that call these services
- **templates/**: Jinja2 templates that render the service data