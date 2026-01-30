# ETL Pipeline Guide for Docker Compose Deployments

This guide explains how to enact the ETL pipeline on a server deployed with Docker Compose to load an empty Couchbase database with data from JSON-L files.

## Overview

When deploying the BOLD Public Portal using Docker Compose, the ETL pipeline loads three types of data into Couchbase:

1. **BCDM data** - Primary specimen/sequence records following the Barcode Core Data Model
2. **Derived data** - Aggregated summaries and accepted search terms
3. **Ancillary data** - Registry information (datasets, taxonomies, institutions, etc.)

## Naturalis Development Server

For the Naturalis installation, connect to the development server and navigate to the Docker Compose project directory:

```bash
# SSH into the development server
ssh dev-bold-app.hosts.naturalis.io

# The .env file is only readable by root, so switch to root user
sudo su

# Navigate to the Docker Compose project directory
cd /opt/compose_projects/fastapi_app/compose
```

All ETL tasks should be executed from this directory where the Docker Compose files and `.env` configuration are located.

**Important:** The Docker Compose configuration maps `/data/import` on the host to `/import` inside the container. When running commands inside the container, use `/import` as the working directory path.

## Prerequisites

### Server Requirements
- Docker and Docker Compose installed
- Sufficient disk space for JSON-L data files (can be several GB compressed)
- Network access to the Couchbase server (or local container)

### Required JSON-L Files

**Primary Data:**
- `bold_singlepane_public_export.jsonl` - BCDM records

**Registries (typically stored compressed in a separate directory):**
- `bold_dataset_registry.jsonl.gz`
- `bold_barcodecluster_registry.jsonl.gz`
- `bold_geopol_registry.jsonl.gz`
- `bold_institution_registry.jsonl.gz`
- `bold_primer_registry.jsonl.gz`
- `bold_taxonomy_registry.jsonl.gz`

### Recommended Directory Structure

On the cluster node hosting the web app and Docker container, data files are organized under `/data`:

```
/data/
├── import_registries/           # Compressed registry files (source data)
│   ├── bold_barcodecluster_registry.jsonl.gz
│   ├── bold_dataset_registry.jsonl.gz
│   ├── bold_geopol_registry.jsonl.gz
│   ├── bold_institution_registry.jsonl.gz
│   ├── bold_primer_registry.jsonl.gz
│   └── bold_taxonomy_registry.jsonl.gz
│
└── import/                      # Working directory with extracted and generated files
    ├── bold_singlepane_public_export.jsonl      # Primary BCDM data
    ├── bold_*_registry.jsonl                    # Extracted registries
    ├── *_summaries.jsonl                        # Generated summaries
    ├── accepted_terms_combined.jsonl            # Combined accepted terms
    ├── accepted_terms_chunk_*.jsonl             # Chunked terms (for large datasets)
    ├── filtered_*_summaries.jsonl               # Filtered summaries (size limit handling)
    ├── reduced_*_summaries.jsonl                # Reduced summaries (for exceptions)
    ├── country_*.json                           # Individual country exception files
    ├── inst_*.json                              # Individual institution exception files
    ├── dataset_*.json                           # Individual dataset exception files
    ├── seq_run_site_*.json                      # Individual sequence run site exception files
    └── *.log                                    # Import and processing logs
```

## Docker Compose Configuration

### Development Environment
Use `docker-compose.yml` which includes a local Couchbase container:
```bash
docker compose up -d
```

### Production Environment
Use `docker-compose-production.yml` which connects to an external Couchbase server:
```bash
docker compose -f docker-compose-production.yml up -d
```

**Note:** The production Docker Compose file does not include Couchbase as it's expected to be hosted externally. You must ensure Couchbase is accessible via the `COUCHBASE_ENDPOINT` environment variable.

## ETL Pipeline Execution Steps

### Step 1: Prepare the Environment

```bash
# Navigate to the Docker Compose project directory (on dev-bold-app.hosts.naturalis.io)
cd /opt/compose_projects/fastapi_app/compose

# Set up environment variables (from .env file)
source .env
export COUCHBASE_ENDPOINT
export COUCHBASE_USER
export COUCHBASE_PASSWORD
export REDIS_HOST

# Data directories on the cluster node (inside /data)
REGISTRY_DIR="/data/import_registries"    # Compressed source registries
WORKING_DIR="/data/import"                 # Working directory for ETL

# Verify directories exist
ls $REGISTRY_DIR
ls $WORKING_DIR
```

### Step 2: Download and Extract Data Files

The registry files are stored compressed in `/data/import_registries`. Extract them to the working directory `/data/import`:

```bash
# Extract primary BCDM data to working directory (if stored compressed)
# gunzip -c $WORKING_DIR/bold_singlepane_public_export.jsonl.gz > $WORKING_DIR/bold_singlepane_public_export.jsonl

# Extract registries from import_registries to import directory
gunzip -c $REGISTRY_DIR/bold_dataset_registry.jsonl.gz > $WORKING_DIR/bold_dataset_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_barcodecluster_registry.jsonl.gz > $WORKING_DIR/bold_barcodecluster_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_geopol_registry.jsonl.gz > $WORKING_DIR/bold_geopol_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_institution_registry.jsonl.gz > $WORKING_DIR/bold_institution_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_primer_registry.jsonl.gz > $WORKING_DIR/bold_primer_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_taxonomy_registry.jsonl.gz > $WORKING_DIR/bold_taxonomy_registry.jsonl
```

**Note:** Using `gunzip -c` preserves the original compressed files in `/data/import_registries` for future reference.

### Step 3: Generate Derived Data (Summaries and Terms)

Generate summary files from the primary BCDM data:

```bash
# Generate summaries and terms from BCDM data
bash src/ETL/generate_and_sanitize_data.sh $WORKING_DIR
```

This script creates the following derived files:
- `tax_geo_inst_summaries.jsonl`
- `country_summaries.jsonl`
- `institution_summaries.jsonl`
- `sequence_run_site_summaries.jsonl`
- `bin_summaries.jsonl`
- `dataset_summaries.jsonl`
- `primer_summaries.jsonl`
- `taxonomy_summaries.jsonl`
- `accepted_terms_combined.jsonl`

### Step 4: Bootstrap Empty Couchbase

#### Option A: Using the Bootstrap Script

For a fresh installation, run the bootstrap script:

```bash
bash src/ETL/couchbase-tools/bootstrap_couchbase.sh $WORKING_DIR
```

This script performs all steps sequentially (collections, data loading, indexes).

#### Option B: Manual Step-by-Step Execution

For more control, execute each step manually:

**Step 4.1: Create Collections**
```bash
python src/ETL/couchbase-tools/run_query.py \
    --endpoint $COUCHBASE_ENDPOINT \
    --username $COUCHBASE_USER \
    --password $COUCHBASE_PASSWORD \
    --file src/ETL/couchbase-tools/couchbase_collections.sql
```

**Step 4.2: Load Primary BCDM Documents**
```bash
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --endpoint $COUCHBASE_ENDPOINT \
    --username $COUCHBASE_USER \
    --password $COUCHBASE_PASSWORD \
    --primary-key 'record_id' \
    --file $WORKING_DIR/bold_singlepane_public_export.jsonl
```

**Step 4.3: Load Derived Documents (Summaries and Terms)**
```bash
# Tax/Geo/Institution summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection tax_geo_inst_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'tax_geo_inst_id' \
    --file $WORKING_DIR/tax_geo_inst_summaries.jsonl

# Country summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection country_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'country/ocean' \
    --file $WORKING_DIR/country_summaries.jsonl

# Institution summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection institution_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'inst' \
    --file $WORKING_DIR/institution_summaries.jsonl

# Sequence run site summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection sequence_run_site_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'sequence_run_site' \
    --file $WORKING_DIR/sequence_run_site_summaries.jsonl

# BIN summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection bin_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'bin_uri' \
    --file $WORKING_DIR/bin_summaries.jsonl

# Dataset summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection dataset_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'dataset.code' \
    --file $WORKING_DIR/dataset_summaries.jsonl

# Primer summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection primer_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'name' \
    --file $WORKING_DIR/primer_summaries.jsonl

# Taxonomy summaries
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection taxonomy_summaries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'taxid' \
    --file $WORKING_DIR/taxonomy_summaries.jsonl

# Accepted terms
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket DERIVED --collection accepted_terms \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'term' \
    --file $WORKING_DIR/accepted_terms_combined.jsonl
```

**Step 4.4: Load Ancillary Documents (Registries)**
```bash
# Datasets registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection datasets \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'dataset.code' \
    --file $WORKING_DIR/bold_dataset_registry.jsonl

# Barcode clusters registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection barcodeclusters \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'barcodecluster.uri' \
    --file $WORKING_DIR/bold_barcodecluster_registry.jsonl

# Countries/geopolitical registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection countries \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'name' \
    --file $WORKING_DIR/bold_geopol_registry.jsonl

# Institutions registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection institutions \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'name' \
    --file $WORKING_DIR/bold_institution_registry.jsonl

# Primers registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection primers \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'name' \
    --file $WORKING_DIR/bold_primer_registry.jsonl

# Taxonomies registry
python src/ETL/couchbase-tools/bulk_load_documents.py \
    --bucket ANCILLARY --collection taxonomies \
    --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD \
    --primary-key 'taxid' \
    --file $WORKING_DIR/bold_taxonomy_registry.jsonl
```

**Step 4.5: Create Indexes**
```bash
python src/ETL/couchbase-tools/run_query.py \
    --endpoint $COUCHBASE_ENDPOINT \
    --username $COUCHBASE_USER \
    --password $COUCHBASE_PASSWORD \
    --file src/ETL/couchbase-tools/couchbase_index_definitions.sql
```

**Step 4.6: Handle Summary Exceptions**

Some summaries may exceed Couchbase's document size limit. Handle these exceptions:
```bash
bash src/ETL/couchbase-tools/update_couchbase_summary_exceptions.sh $WORKING_DIR
```

### Step 5: Initialize Redis Cache

After loading Couchbase, populate the Redis cache for optimal performance:

```bash
python src/tools/generateSummaryCache.py -i src/tools/summary_cache_queries.json
python src/tools/generateTaxMapCache.py -i src/tools/tax_map_cache_queries.json
python src/tools/generateStatsCache.py
```

### Step 6: Verify the Installation

Test the Couchbase connection:
```bash
python src/ETL/couchbase-tools/run_query.py \
    --endpoint $COUCHBASE_ENDPOINT \
    --username $COUCHBASE_USER \
    --password $COUCHBASE_PASSWORD \
    --file src/ETL/couchbase-tools/query_to_check_connection.n1ql
```

## Running ETL Inside Docker Containers

The ETL pipeline runs on the cluster node where `/data/import` and `/data/import_registries` are located. The Docker Compose configuration maps `/data/import` on the host to `/import` inside the container.

### Method 1: Execute on the FastAPI Container

On the Naturalis development server, the container is named `compose-fastapi-app-1`:

```bash
# First, ensure you are root (required to read .env file)
sudo su

# Navigate to the Docker Compose project directory
cd /opt/compose_projects/fastapi_app/compose

# Execute a shell inside the container
# Note: /data/import on host is mounted as /import inside the container
docker exec -it compose-fastapi-app-1 bash

# Inside the container, the data files are available at /import
ls /import
```

To run the bootstrap script inside the container:
```bash
docker exec -it compose-fastapi-app-1 bash -c "
    bash /app/src/ETL/couchbase-tools/bootstrap_couchbase.sh /import
"
```

### Method 2: Run a Dedicated ETL Container

Create a one-off container for ETL operations. Note that `/data/import` on the host should be mounted to `/import` inside the container to match the existing configuration:

```bash
# For production deployment on Naturalis server (project name is 'compose')
docker run --rm \
    --network compose_backend-production \
    -v /data/import:/import \
    -v $(pwd):/app \
    -w /app \
    --env-file .env \
    fastapi-app:latest \
    bash src/ETL/couchbase-tools/bootstrap_couchbase.sh /import

# For development deployment on Naturalis server
docker run --rm \
    --network compose_backend \
    -v /data/import:/import \
    -v $(pwd):/app \
    -w /app \
    --env-file .env \
    fastapi-app:latest \
    bash src/ETL/couchbase-tools/bootstrap_couchbase.sh /import
```

**Note:** The network name format is `<project-name>_<network-name>`. On the Naturalis server (`dev-bold-app.hosts.naturalis.io`), the project name is `compose`, so the networks are `compose_backend` and `compose_backend-production`.

## Couchbase Bucket Structure

After the ETL pipeline completes, Couchbase will have the following structure:

```
BCDM (bucket)
└── _default (scope)
    └── primary (collection) - BCDM specimen/sequence records

DERIVED (bucket)
└── _default (scope)
    ├── accepted_terms - Search terms
    ├── tax_geo_inst_summaries - Taxonomy/geography/institution aggregates
    ├── country_summaries - Country-level summaries
    ├── institution_summaries - Institution-level summaries
    ├── sequence_run_site_summaries - Sequencing site summaries
    ├── bin_summaries - BIN (Barcode Index Number) summaries
    ├── dataset_summaries - Dataset summaries
    ├── primer_summaries - Primer summaries
    └── taxonomy_summaries - Taxonomy summaries

ANCILLARY (bucket)
└── _default (scope)
    ├── datasets - Dataset registry
    ├── barcodeclusters - Barcode cluster registry
    ├── countries - Geopolitical registry
    ├── institutions - Institution registry
    ├── primers - Primer registry
    └── taxonomies - Taxonomy registry
```

## Troubleshooting

### Connection Issues
- Verify `COUCHBASE_ENDPOINT` points to the correct Couchbase server
- Ensure network connectivity between the ETL host and Couchbase
- Check that the Couchbase user has appropriate permissions

### Memory Issues
- For large datasets, increase the batch size in `bulk_load_documents.py`
- Monitor Couchbase memory usage and adjust bucket RAM quotas if needed

### Document Size Errors
- Documents exceeding 20MB will be filtered automatically
- Check the `update_couchbase_summary_exceptions.sh` script for handling large summaries

## Related Documentation

- [QUARTERLY_REBUILD_SOP.md](QUARTERLY_REBUILD_SOP.md) - Full quarterly rebuild procedure
- [WEEKLY_REBUILD_SOP.md](WEEKLY_REBUILD_SOP.md) - Weekly update procedure
- [REBUILD_DESIGN.md](REBUILD_DESIGN.md) - ETL pipeline design overview
- [couchbase-tools/README.md](couchbase-tools/README.md) - Couchbase tools documentation
