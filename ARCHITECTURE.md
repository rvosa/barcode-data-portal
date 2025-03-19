# BOLD Public Portal Architecture

This document provides an overview of the BOLD (Barcode of Life Data) Public Portal architecture. It serves as an entry point for developers to understand the system design, component interactions, and key technical decisions.

## System Overview

The BOLD Public Portal is a web application that provides public access to biodiversity data through a REST API and web interface. It serves as a platform for researchers, students, and the general public to explore genetic barcode data for various species.

The application follows a modern layered architecture with:
- API-first design
- Clear separation of concerns
- Comprehensive caching strategies for performance
- Headless CMS integration

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Primary Database**: Couchbase (NoSQL)
- **Source Database**: PostgreSQL (Data Submission Workbench)
- **Caching**: Redis
- **Frontend**: Jinja2 templates with JavaScript/jQuery
- **Content Management**: WordPress (Headless)
- **Testing**: Cypress (End-to-End)

## Database Architecture

The BOLD system uses a dual-database architecture:

1. **PostgreSQL**: The primary database for the Data Submission Workbench (a separate system) where data is initially collected, curated, and managed.

2. **Couchbase**: The database powering the Public Portal, populated through ETL processes from PostgreSQL. This NoSQL document store provides:
   - Flexible schema for biodiversity data
   - High-performance querying capabilities
   - Document-oriented storage optimized for the Public Portal use cases

Data flows from PostgreSQL to Couchbase through ETL processes that extract, transform, and load data on weekly and quarterly schedules. This separation allows the internal submission workbench to operate independently from the public-facing portal.

## Directory Structure

```
src/
├── cypress/               # End-to-end testing
│   ├── e2e/               # End-to-end tests by component
│   │   ├── services/      # Tests for API services
│   │   └── views/         # Tests for web views
│   ├── user_journey/      # End-to-end user flow tests
│   └── templates/         # Templates for new tests
├── ETL/                   # Extract, Transform, Load pipelines
│   ├── couchbase-tools/   # Tools for Couchbase operations
│   └── postprocess/       # Post-processing scripts
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

#### Source Database: PostgreSQL
- Primary database for the Data Submission Workbench
- Contains the authoritative source data
- Not directly accessed by the Public Portal

#### Public Database: Couchbase
- Stores primary biodiversity data and pre-computed summaries
- NoSQL document store allows for flexible schema
- Designed for high-performance querying
- Populated from PostgreSQL via ETL processes

#### Data Access Object (DAO)
- `dao.py`: Centralized interface for database operations
- Implements query methods for various data types
- Manages database connections and query formatting

#### ETL Pipeline
- Located in the `ETL/` directory
- Extracts data from BOLD's internal PostgreSQL database
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

### 2. Comprehensive Caching Strategy

The application implements a multi-layered caching approach to optimize performance:

#### Redis In-Memory Caching
- Stores frequently accessed data in memory for fastest retrieval
- Caches structured query results with configured TTL (Time-To-Live)
- Used for API responses, autocomplete data, and term lookups
- Managed through utility functions in `util.py`

#### Pre-computed Summary Documents
- Generated during ETL processes and stored in Couchbase
- Provide aggregated data for common dimensions (taxonomy, geography, etc.)
- Enable fast retrieval of dashboard and visualization data
- Updated on weekly and quarterly schedules

#### File-Based Query Result Caching
- Used for larger result sets that exceed Redis memory limits
- Implemented for document downloads and complex query results
- Identified by encoded query IDs for efficient lookup
- Managed by tools in the `tools/` directory

#### Cache Generation Tools
- Located in the `tools/` directory
- Pre-warm caches for common queries
- Generate and store summarized data
- Include specialized tools for maps, taxonomy trees, and statistics

#### Client-Side Caching
- Static assets configured with appropriate HTTP cache headers
- Browser caching for JS, CSS, and images
- Client-side storage for user preferences and recent searches

This layered approach ensures optimal performance across the application while balancing memory usage and data freshness requirements.

### 3. Headless CMS Integration

The application integrates with WordPress as a headless CMS:

- Content is authored in WordPress
- Templates include WordPress-generated HTML
- Static assets from WordPress are served directly
- Consistent styling between CMS and application content

**Note**: The exact implementation details of the WordPress integration require further clarification from the BOLD designers at CBG in Guelph.

## Data Flow

### 1. Request Handling Flow

1. HTTP request arrives at `main.py`
2. Request is routed to appropriate view or service
3. Controller processes the request parameters
4. DAO methods retrieve data from Couchbase
5. Data is transformed to appropriate response format
6. Response is returned to the client

### 2. ETL Data Flow

1. Data is extracted from BOLD's internal PostgreSQL database
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
- Implementation of CI/CD pipeline based on prior art developed at Naturalis in Leiden
- Improved automated testing integration

## Related Documentation

- `src/README.md`: Overview of the source code directory
- `src/services/README.md`: Details on API services
- `src/views/README.md`: Information on view controllers
- `src/templates/README.md`: Template system documentation
- `src/ETL/README.md`: ETL process documentation
- `src/cypress/README.md`: Testing framework documentation