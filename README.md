# BOLD Public Portal

## Overview
The Barcode of Life Data (BOLD) Portal is a web application and database designed to support the access, querying, and dissemination of DNA barcode data. DNA barcodes are standardized genetic markers used for species identification, with each record uniquely linking sequence data to specimen information, images, and provenance. Built on open-source technologies—including Couchbase, FastAPI, Redis, and Python—the application provides a scalable and high-performance infrastructure for managing barcode data. Its database follows the Barcode Core Data Model (BCDM - https://github.com/DNAdiversity/BCDM), ensuring structured and interoperable data representation.

The BOLD Portal is designed for multi-institutional deployment, enabling data mirroring and supporting data sovereignty requirements. It includes critical functionalities for monitoring and managing DNA reference libraries through National and Institutional Dashboards, facilitating real-time oversight of barcode repositories. Additionally, the system hosts published datasets, allowing users to download and integrate them into local analytical pipelines.

Developed with an API-first architecture, the application provides a robust API that enables seamless extensions without modifications to the core codebase. Released under the AGPL license, the BOLD Portal promotes open access, collaboration, and interoperability within the global biodiversity informatics community.

## Database Architecture

The BOLD system uses a dual-database architecture:

- **PostgreSQL**: Primary database for the Data Submission Workbench (a separate system) where data is initially collected, curated, and managed by researchers.

- **Couchbase**: NoSQL database powering the Public Portal, populated through scheduled ETL processes from PostgreSQL. Optimized for high-performance querying and flexible document schema to support the portal's needs.

Data flows from PostgreSQL to Couchbase through ETL processes that run on weekly and quarterly schedules.

## Requirements

- Docker
- NGINX
- Python: FastAPI and Socketserver Logger
- Redis and File System Cache
- Couchbase
- Barcode Core Data Model

Dependencies:
- Barcode Core Data Model repository
- SSL Certificates
- Maintenance job to clear File System Cache
  - `find /tmp/bold-public-portal/cache -type f -amin +1440 -delete`

## Local Deployment

Requirements:
- [Docker Desktop](https://docs.docker.com/desktop/)
- [Tilt](https://docs.tilt.dev/install.html)

```bash
REPO_DIR="barcode-data-portal"

# Spool Up
cd $REPO_DIR
tilt up -f docker/Tiltfile

# Spool Down
cd $REPO_DIR
tilt down -f docker/Tiltfile

# Check Status
# Go to http://localhost:10350/overview
```

## Production Deployment

Check that `.env` is configured correctly and to production values. The following assumes the ansible playbook is not being used and Couchbase is hosted on a different server.

```bash
REPO_DIR="barcode-data-portal"

# Spool Up
cd $REPO_DIR
docker build -t fastapi-app -f docker/Dockerfile .
docker build -t socketserver-logging -f docker/Dockerfile.socketserver_logging .
docker compose -f docker-compose-production.yml up -d

# Spool Down
cd $REPO_DIR
docker compose -f docker-compose-production.yml down

# Check Status
docker ps -a
```

Alternatively, if the use of screens are required instead of Docker containers:
```bash
systemctl start nginx
systemctl start redis

screen -S fastapi-app
cd $REPO_DIR/src
gunicorn main:app --workers 24 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000

screen -S socketserver-logging
cd $REPO_DIR/src
python socketserver_logging.py
```

## Testing

See `CYPRESS.md`

## File Organization

- `db_data`
  - Local simulated database data
- `docker`
  - Docker and Tilt components
- `src`
  - Main source code
  - `cypress`
    - Cypress testing configuration
    - `e2e`
      - `services`  # Tests for API services
      - `views`     # Tests for web views
    - `user_journey` # End-to-end user flow tests
    - `plugins`      # Cypress plugins configuration
    - `support`      # Support files and custom commands
    - `templates`    # Templates for creating new tests
  - `ETL`
    - Data (BCDM) extraction, transformation, and loading
    - `couchbase-tools` # Tools for Couchbase operations
    - `postprocess`     # Post-processing scripts
  - `services`
    - API services; serve the application data but can also be used independently
  - `static`
    - Assets for application presentation
    - `css`          # CSS stylesheets
    - `js`           # JavaScript files
    - `img`          # Images and media
    - `wp-content`   # WordPress content assets
    - `wp-includes`  # WordPress core assets
    - `wp-json`      # WordPress API responses
  - `templates`
    - Jinja2/HTML application layout
    - `includes`     # Reusable template components
    - `wp-templates` # WordPress content templates
  - `tools`
    - Miscellaneous tools for the application
  - `views`
    - Application view controllers

## WordPress Integration

The BOLD Public Portal integrates with WordPress as a headless CMS. This allows content to be authored in WordPress while being displayed seamlessly within the application.

**Note**: The exact implementation details of the WordPress integration require further clarification from the BOLD designers at CBG in Guelph.

## Citation

@misc{Ratnasingham2025BOLD5,
    title={BOLD5: A Comprehensive Suite of Applications to Support the Assembly, Preservation, and Application of DNA Barcode Libraries}, 
    author={Sujeevan Ratnasingham, Jireh Agda, Catherine Wei and Josh Agda, Chris Ho, Sameer Padhye, Shweta Purushe, Spandana Chereddy, Spencer Moncton, Dana Rea, Ejhtiar Islam, Paul Hebert},
    institution={Centre for Biodiversity Genomics},
    year={2025}
}