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

## Service Modules and Endpoints

### ancillary.py
Retrieves metadata and reference information from ancillary collections.

### counts.py
Generates metadata count statistics for queries.

### documents.py
Retrieves and formats document data, handles downloads in various formats.

### images.py
Retrieves and processes image metadata and URLs.

### maps.py
Generates geographic maps based on coordinate data.

### qr.py
Generates QR codes for sequences and records.

### query.py
Handles the main search functionality, storing results in cache.

### query_parse.py
Parses free-text queries into structured triplet format.

### query_preprocessor.py
Resolves and expands query terms to match database entries.

### stats.py
Provides general statistics about the database.

### summary.py
Generates metadata summaries by aggregating fields from documents.

### taxonomy.py
Retrieves and processes taxonomic data, hierarchies, and maps.

### terms.py
Handles term lookup and autocompletion functionality.

### test.py
Simple test endpoints for service validation.

For specific endpoint details, parameters, and response formats, please refer to the automatically generated API documentation available at:
- `/api/docs` (Swagger UI)
- `/api/redoc` (ReDoc)

When running the application locally, these documentation endpoints provide comprehensive information about all available API endpoints, including request parameters, response schemas, and example usage.

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

This format provides a consistent interface across the application and allows for precise data targeting.

### Caching Strategy

The services implement a comprehensive multi-level caching strategy as defined in the architecture:

#### Redis In-Memory Caching
- Stores frequently accessed data in memory for fastest retrieval
- Caches structured query results with configured TTL (Time-To-Live)
- Used for API responses, autocomplete data, and term lookups
- Managed through utility functions in [util.py](../util.py)

#### Pre-computed Summary Documents
- Generated during ETL processes and stored in Couchbase
- Provide aggregated data for common dimensions (taxonomy, geography, etc.)
- Enable fast retrieval of dashboard and visualization data
- Updated on weekly and quarterly schedules

#### File-Based Query Result Caching
- Used for larger result sets that exceed Redis memory limits
- Implemented for document downloads and complex query results
- Identified by encoded query IDs for efficient lookup
- Managed by tools in the [tools](../tools) directory

#### Client-Side Caching
- Static assets configured with appropriate HTTP cache headers
- Browser caching for JS, CSS, and images

## Integration with Overall Architecture

The services layer:

1. **Consumes from**:
   - FastAPI routing system
   - DAO layer ([dao.py](../dao.py)) for database access
   - Utility functions ([util.py](../util.py)) for caching and query processing

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

- [dao.py](../dao.py): Data Access Object that services use to interact with the database
- [util.py](../util.py): Utility functions for caching, query processing, and security
- [views](../views): Web view controllers that call these services
- [templates](../templates): Jinja2 templates that render the service data