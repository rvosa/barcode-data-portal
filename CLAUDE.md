# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The BOLD (Barcode of Life Data) Public Portal is a FastAPI-based web application providing public access to DNA barcode data for species identification. It uses Couchbase as the primary database (populated via ETL from PostgreSQL), Redis for caching, and follows an API-first architecture with Jinja2 templates for the web interface.

The system is designed for multi-institutional deployment with data sovereignty support, hosting published DNA barcode datasets for biodiversity research.

## Development Setup

### Local Development with Tilt

```bash
# Start local development environment
tilt up -f docker/Tiltfile

# Check status at http://localhost:10350/overview

# Stop environment
tilt down -f docker/Tiltfile
```

Tilt orchestrates Docker Compose and provides live reloading for development. Changes to `src/` files automatically sync to containers.

### Production Deployment

```bash
# Build images
docker build -t fastapi-app -f docker/Dockerfile .
docker build -t socketserver-logging -f docker/Dockerfile.socketserver_logging .

# Deploy
docker compose -f docker-compose-production.yml up -d
```

Ensure `.env` is configured with production values before deployment.

## Common Commands

### Testing

```bash
# Run Cypress end-to-end tests (from src/cypress/)
cd src/cypress
npm install
npx cypress run --config-file cypress.config.js

# Run specific test
npx cypress run --config-file cypress.config.js --spec PATH_TO_TEST/test.cy.js
```

Update `baseUrl` in `cypress.config.js` to point to your test environment (default: `http://localhost:8000`).

### Code Quality (CI Pipeline)

The project uses GitLab CI with the following linters:

```bash
# Format code with black
black .

# Check imports with isort
isort .

# Lint with flake8
flake8 .
```

These run automatically in CI but can be executed locally for validation.

### Cache Management

Pre-warm caches for optimal performance:

```bash
# Generate general statistics cache
python src/tools/generateStatsCache.py

# Generate summary cache for specific queries
python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json

# Generate taxonomy map cache
python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json
```

### Couchbase Connection Testing

```bash
# Test database connectivity
python src/tools/test_couchbase_connect.py

# Test document downloads
python src/tools/test_couchbase_download.py
```

## Architecture Overview

### Layered Architecture

```
Views (web pages) → Services (API) → DAO (data access) → Couchbase
                                   ↓
                              Redis Cache
```

- **Views** (`src/views/`): FastAPI routes rendering Jinja2 templates, calling services via internal HTTP
- **Services** (`src/services/`): REST API endpoints with business logic, documented at `/api/docs`
- **DAO** (`src/dao.py`): Centralized database access layer for Couchbase queries
- **Templates** (`src/templates/`): Jinja2 HTML templates with includes and WordPress integration
- **Static Assets** (`src/static/`): CSS, JavaScript, images, and WordPress content

### Database Architecture

**Dual-database design:**
- **PostgreSQL**: Source database (Data Submission Workbench) - not accessed by Public Portal
- **Couchbase**: Public Portal database with three buckets:
  - `BCDM.primary`: Main specimen/sequence data in BCDM format
  - `DERIVED.*_summaries`: Pre-computed aggregations (taxonomy, geography, institutions)
  - `ANCILLARY.*`: Reference data (datasets, barcode clusters, publications)

Data flows from PostgreSQL → ETL → Couchbase on weekly/quarterly schedules.

### ETL Pipeline

Located in `src/ETL/`:
- **Weekly updates**: Incremental data refresh (Sundays at 00:00 UTC)
- **Quarterly bootstrap**: Full database rebuild (Jan/Apr/Jul/Oct)

Main ETL orchestration: `generate_and_sanitize_data.sh`

Key scripts:
- `export_singlepane_view.py`: Extract from PostgreSQL
- `extract_bold4_singlepane_to_BCDM.py`: Transform to BCDM format
- `extract_*_summary.py`: Generate pre-computed summaries
- `filter_barcodeclusters_based_on_bcdm.py`: Apply data policies

After ETL completion, run cache warming scripts in `src/tools/`.

### Caching Strategy

Multi-layered approach for performance:

1. **Redis**: Frequently accessed queries, autocomplete, term lookups (TTL-based)
2. **Pre-computed summaries**: Generated during ETL, stored in Couchbase
3. **File-based cache**: Large result sets in `/tmp/bold-public-portal/cache` (cleared by maintenance job: `find /tmp/bold-public-portal/cache -type f -amin +1440 -delete`)
4. **Client-side**: Browser caching for static assets

Cache utilities in `src/util.py`.

### Triplet Query Format

The system uses `scope:subscope:value` format for structured queries:
- `tax:species:Homo sapiens` (taxonomy)
- `geo:country:Canada` (geography)
- `bin:uri:BOLD:AAA1234` (Barcode Index Number)

This format is used throughout services, DAO, and ETL.

## Key Files

- `src/main.py`: FastAPI application entry point, route registration, middleware
- `src/settings.py`: Configuration management (env vars, paths, database connections)
- `src/dao.py`: Data Access Object with Couchbase query methods
- `src/util.py`: Shared utilities (caching, security, query processing)
- `src/socketserver_logging.py`: Centralized logging service
- `src/logging.ini`: Logging configuration

## Configuration

Environment variables (`.env`):
- `COUCHBASE_ENDPOINT`: Couchbase connection string (default: `couchbase://couchbase`)
- `COUCHBASE_USER`, `COUCHBASE_PASSWORD`: Database credentials
- `APP_NAME`: Application identifier (default: `fastapi-app`)
- `APP_PORT`: Service port (default: `8000`)

Redis and cache paths configured in `settings.py`.

## WordPress Integration

The portal integrates WordPress as a headless CMS:
- Content authored in WordPress, served through the portal
- Static assets in `src/static/wp-content/`, `wp-includes/`, `wp-json/`
- Templates in `src/templates/wp-templates/`

WordPress content appears seamlessly within the application layout.

## Development Workflow

1. Make code changes in `src/`
2. Tilt auto-reloads containers (or manually restart services)
3. Run Cypress tests to validate
4. Format with `black` and check with `isort`/`flake8`
5. Commit to feature branch (main branch: `develop`)
6. CI pipeline runs linting and tests
7. Deploy to staging, validate with production-like data
8. Deploy to production

## Important Notes

- **Never access PostgreSQL directly** from the Public Portal - all data comes from Couchbase via ETL
- **Always use DAO methods** for database queries - don't write raw Couchbase queries in services/views
- **Maintain cache consistency** - invalidate Redis cache when ETL updates data
- **Test with realistic data** - local development uses `db_data/` sample data, staging uses production subset
- **API documentation** is auto-generated at `/api/docs` (Swagger) and `/api/redoc`
- **The main branch is `develop`** - create PRs targeting this branch

## Security Considerations

- Query validation in services prevents injection attacks
- Large queries are paginated to prevent resource exhaustion
- Data policies applied during ETL filter protected/embargoed records
- File-based cache requires periodic cleanup to prevent disk exhaustion