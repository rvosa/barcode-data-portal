# BOLD Public Portal Architecture

This document provides an overview of the BOLD (Barcode of Life Data) Public Portal architecture. It serves as an entry point for developers to understand the system design, component interactions, and key technical decisions.

## System Overview

The BOLD Public Portal is a web application that provides public access to biodiversity data through a REST API and web interface. It serves as a platform for researchers, students, and the general public to explore genetic barcode data for various species.

The application follows a modern layered architecture with:
- API-first design
- Clear separation of concerns
- Caching strategies for performance
- Headless CMS integration

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: Couchbase (NoSQL)
- **Caching**: Redis
- **Frontend**: Jinja2 templates with JavaScript/jQuery
- **Content Management**: WordPress (Headless)
- **Testing**: Cypress (End-to-End)

## Directory Structure

```
src/
├── cypress/               # End-to-end testing
├── ETL/                   # Extract, Transform, Load pipelines
├── services/              # API service implementations
├── static/                # Static web assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   ├── img/               # Images
│   ├── wp-content/        # WordPress content assets
│   ├── wp-includes/       # WordPress core assets
│   └── wp-json/           # WordPress API responses
├── templates/             # Jinja2 templates
│   ├── includes/          # Reusable template components
│   └── wp-templates/      # WordPress content templates
├── tools/                 # Utility scripts and tools
├── views/                 # Web view controllers
├── dao.py                 # Data Access Object
├── main.py                # Application entry point
├── settings.py            # Configuration settings
├── util.py                # Utility functions
└── [logging configuration files]
```

## Core Components

### 1. Data Layer

#### Database: Couchbase
- Stores primary biodiversity data and pre-computed summaries
- NoSQL document store allows for flexible schema
- Designed for high-performance querying

#### Data Access Object (DAO)
- `dao.py`: Centralized interface for database operations
- Implements query methods for various data types
- Manages database connections and query formatting

#### ETL Pipeline
- Located in the `ETL/` directory
- Extracts data from BOLD's internal database
- Transforms it into optimized documents
- Loads data into Couchbase
- Generates summary and terms collections
- Runs on weekly and quarterly schedules

### 2. Service Layer

Located in the `services/` directory, these are the RESTful API endpoints:

- **Query Services**: Search and retrieve biodiversity records
  - `query.py`: Main search endpoint
  - `query_parse.py`: Parses natural language to structured queries
  - `query_preprocessor.py`: Resolves query terms

- **Data Services**: Retrieve specific data types
  - `documents.py`: Retrieve document records
  - `summary.py`: Get aggregated data summaries
  - `taxonomy.py`: Taxonomy-specific endpoints
  - `images.py`: Image metadata and URLs
  - `maps.py`: Geographic visualization data

- **Utility Services**: Supporting functionality
  - `terms.py`: Term lookup and autocompletion
  - `qr.py`: QR code generation
  - `stats.py`: Statistical information

### 3. Presentation Layer

#### View Controllers
Located in the `views/` directory, these handle web page rendering:

- Page-specific controllers (index, record, bin, etc.)
- Fetch data from services
- Render templates with context
- Handle URL routing

#### Templates
Located in the `templates/` directory:

- Base templates for consistent layout
- Page-specific templates extending the base
- Component templates for reusable UI elements
- WordPress content integration templates

#### Static Assets
Located in the `static/` directory:

- CSS for styling
- JavaScript for client-side functionality
- Images and other media
- WordPress integrated assets

### 4. Utility Components

- `util.py`: Common functions used across the application
- `settings.py`: Application configuration
- `tools/`: Scripts for maintenance and operations
- `logging.ini` and related files: Logging configuration

### 5. Testing Framework

Located in the `cypress/` directory:

- End-to-end tests for web interface
- API tests for service endpoints
- User journey tests for common workflows
- Templates for creating new tests

## Key Patterns

### 1. Triplet Query Format

The application uses a "triplet" query format (`scope:subscope:value`) for structured data queries:
- `tax:species:Homo sapiens` (Taxonomy scope, species rank, value "Homo sapiens")
- `geo:country:Canada` (Geography scope, country subscope, value "Canada")
- `bin:uri:BOLD:AAA1234` (BIN scope, URI subscope, value "BOLD:AAA1234")

This format provides a consistent interface across the application and allows for precise data targeting.

### 2. Multi-level Caching Strategy

The application implements several caching layers for performance:

- **Redis Caching**: In-memory caching for frequently accessed data
- **Pre-computed Summaries**: Generated during ETL for fast retrieval
- **Query Result Caching**: Cached results for common queries
- **Client-side Caching**: Browser caching for static assets

### 3. Headless CMS Integration

The application integrates with WordPress as a headless CMS:

- Content is authored in WordPress
- Templates include WordPress-generated HTML
- Static assets from WordPress are served directly
- Consistent styling between CMS and application content

## Data Flow

### 1. Request Handling Flow

1. HTTP request arrives at `main.py`
2. Request is routed to appropriate view or service
3. Controller processes the request parameters
4. DAO methods retrieve data from Couchbase
5. Data is transformed to appropriate response format
6. Response is returned to the client

### 2. ETL Data Flow

1. Data is extracted from BOLD's internal database
2. Raw data is transformed into standardized BCDM format
3. Summary documents are generated for key dimensions
4. Terms are extracted and indexed for search
5. Documents are loaded into Couchbase
6. Cache is warmed for common queries

## Deployment Considerations

### Environment Configuration

The application uses `settings.py` for configuration management:
- Database connections
- File paths
- Application settings
- Environment-specific settings

### Logging

Logging is implemented with:
- Socket-based logging for centralization
- File rotation for persistent logs
- Separate logs for different concerns (exceptions, queries, access)

### Performance Optimization

- Static assets should be served via a CDN
- Nginx should be configured for reverse proxy
- Couchbase cluster sizing should account for data volume
- Redis should be sized for caching requirements

## Development Workflow

1. Make changes to code
2. Run Cypress tests to validate changes
3. Test with development data
4. Deploy to staging environment
5. Verify with production-like data
6. Deploy to production

## Future Architecture Considerations

- Migration to a more modern frontend framework (React/Vue)
- Expanded microservice architecture
- Enhanced caching strategies
- GraphQL API layer

## Related Documentation

- `src/README.md`: Overview of the source code directory
- `src/services/README.md`: Details on API services
- `src/views/README.md`: Information on view controllers
- `src/templates/README.md`: Template system documentation
- `src/ETL/README.md`: ETL process documentation
- `src/cypress/README.md`: Testing framework documentation