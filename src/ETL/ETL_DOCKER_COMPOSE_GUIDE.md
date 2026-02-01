# ETL Pipeline Guide for Docker Compose Deployments

This guide explains how to enact the ETL pipeline on a server deployed with Docker Compose to load an empty Couchbase database with data from JSON-L files.

## Overview

When deploying the BOLD Public Portal using Docker Compose, the ETL pipeline loads three types of data into Couchbase:

1. **BCDM data** - Primary specimen/sequence records following the Barcode Core Data Model
2. **Derived data** - Aggregated summaries and accepted search terms
3. **Ancillary data** - Registry information (datasets, taxonomies, institutions, etc.)

## Naturalis Development Server

For the Naturalis installation, connect to the development server:

```bash
# SSH into the development server
ssh dev-bold-app.hosts.naturalis.io

# The .env file is only readable by root, so switch to root user
sudo su

# Navigate to the Docker Compose project directory
cd /opt/compose_projects/fastapi_app/compose
```

**Volume Mapping:** The Docker Compose configuration maps `/data/import` on the host to `/import` inside the container.

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

### Directory Structure

On the cluster node, data files are organized under `/data`:

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

## Running ETL Inside the Docker Container

On the Naturalis development server, the container is named `compose-fastapi-app-1`. All ETL commands are run inside this container from the `/app` working directory.

### Accessing the Container

```bash
# First, ensure you are root (required to read .env file)
sudo su

# Navigate to the Docker Compose project directory
cd /opt/compose_projects/fastapi_app/compose

# Execute a shell inside the container
docker exec -it compose-fastapi-app-1 bash

# You are now at /app inside the container
# Data files are available at /import (mapped from /data/import on host)
```

### Step 1: Extract Registry Files (on host, before entering container)

Extract the registry files from `/data/import_registries` to `/data/import`:

```bash
# Run these commands on the host (not inside the container)
REGISTRY_DIR="/data/import_registries"
WORKING_DIR="/data/import"

gunzip -c $REGISTRY_DIR/bold_dataset_registry.jsonl.gz > $WORKING_DIR/bold_dataset_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_barcodecluster_registry.jsonl.gz > $WORKING_DIR/bold_barcodecluster_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_geopol_registry.jsonl.gz > $WORKING_DIR/bold_geopol_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_institution_registry.jsonl.gz > $WORKING_DIR/bold_institution_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_primer_registry.jsonl.gz > $WORKING_DIR/bold_primer_registry.jsonl
gunzip -c $REGISTRY_DIR/bold_taxonomy_registry.jsonl.gz > $WORKING_DIR/bold_taxonomy_registry.jsonl
```

### Step 2: Generate Derived Data

Run `ETL/generate_and_sanitize_data.sh` inside the container. This script generates all summary files from the primary BCDM data.

```bash
# Inside the container (working directory is /app)
WORKING_DIR="/import"
nohup bash ETL/generate_and_sanitize_data.sh $WORKING_DIR &

# Check progress
tail -f nohup.out
```

**This script performs the following steps internally:**

1. Applies BCDM policies to filter records (`ETL/apply_BCDM_policies.sh`)
2. Extracts terms and tax/geo/inst summaries (`python ETL/extract_terms_and_summary_from_BCDM.py`)
3. Extracts additional terms (`python ETL/extract_minimized_terms_with_inst_bins_ids_codes_BCDM.py`)
4. Generates country summaries (`python ETL/extract_country_summary.py`)
5. Generates institution summaries (`python ETL/extract_institution_summary.py`)
6. Generates sequence run site summaries (`python ETL/extract_sequence_run_site_summary.py`)
7. Generates BIN summaries (`python ETL/extract_bin_summary.py`)
8. Generates dataset summaries (`python ETL/extract_dataset_summary.py`)
9. Generates primer summaries (`python ETL/extract_primer_summary.py`)
10. Sanitizes registry documents (filters empty names, handles UTF-8 encoding)
11. Generates taxonomy summaries (`python ETL/extract_taxonomy_summary.py`)

**Output files created:**
- `tax_geo_inst_summaries.jsonl`
- `country_summaries.jsonl` + `filtered_country_summaries.jsonl` + `reduced_country_summaries.jsonl`
- `institution_summaries.jsonl` + `filtered_institution_summaries.jsonl` + `reduced_institution_summaries.jsonl`
- `sequence_run_site_summaries.jsonl` + `filtered_sequence_run_site_summaries.jsonl` + `reduced_sequence_run_site_summaries.jsonl`
- `bin_summaries.jsonl` + `filtered_bin_summaries.jsonl` + `reduced_bin_summaries.jsonl`
- `dataset_summaries.jsonl` + `filtered_dataset_summaries.jsonl` + `reduced_dataset_summaries.jsonl`
- `primer_summaries.jsonl` + `filtered_primer_summaries.jsonl` + `reduced_primer_summaries.jsonl`
- `taxonomy_summaries.jsonl`
- `accepted_terms_combined.jsonl`

### Step 3: Bootstrap Couchbase

Run `ETL/couchbase-tools/bootstrap_couchbase.sh` inside the container. This script loads all data into Couchbase.

```bash
# Inside the container (working directory is /app)
WORKING_DIR="/import"
nohup bash ETL/couchbase-tools/bootstrap_couchbase.sh $WORKING_DIR &

# Check progress
tail -f nohup.out
```

**This script performs the following steps internally:**

1. **Create collections** (`python ETL/couchbase-tools/run_query.py` with `couchbase_collections.sql`)

2. **Load primary BCDM documents** (`python ETL/couchbase-tools/bulk_load_documents.py`)
   - Loads `bold_singlepane_public_export.jsonl` into `BCDM.primary`

3. **Load derived summaries and terms** (`python ETL/couchbase-tools/bulk_load_documents.py` for each):
   - `tax_geo_inst_summaries.jsonl` → `DERIVED.tax_geo_inst_summaries`
   - `country_summaries.jsonl` → `DERIVED.country_summaries`
   - `institution_summaries.jsonl` → `DERIVED.institution_summaries`
   - `sequence_run_site_summaries.jsonl` → `DERIVED.sequence_run_site_summaries`
   - `bin_summaries.jsonl` → `DERIVED.bin_summaries`
   - `dataset_summaries.jsonl` → `DERIVED.dataset_summaries`
   - `primer_summaries.jsonl` → `DERIVED.primer_summaries`
   - `taxonomy_summaries.jsonl` → `DERIVED.taxonomy_summaries`
   - `accepted_terms_combined.jsonl` → `DERIVED.accepted_terms`

4. **Load ancillary registry documents** (`python ETL/couchbase-tools/bulk_load_documents.py` for each):
   - `bold_dataset_registry.jsonl` → `ANCILLARY.datasets`
   - `bold_barcodecluster_registry.jsonl` → `ANCILLARY.barcodeclusters`
   - `bold_geopol_registry.jsonl` → `ANCILLARY.countries`
   - `bold_institution_registry.jsonl` → `ANCILLARY.institutions`
   - `bold_primer_registry.jsonl` → `ANCILLARY.primers`
   - `bold_taxonomy_registry.jsonl` → `ANCILLARY.taxonomies`

5. **Create indexes** (`python ETL/couchbase-tools/run_query.py` with `couchbase_index_definitions.sql`)

### Step 4: Initialize Redis Cache

After loading Couchbase, populate the Redis cache:

```bash
# Inside the container (working directory is /app)
python tools/generateSummaryCache.py -i tools/summary_cache_queries.json
python tools/generateTaxMapCache.py -i tools/tax_map_cache_queries.json
python tools/generateStatsCache.py
```

### Step 5: Verify the Installation

Test the Couchbase connection:

```bash
# Inside the container (working directory is /app)
python ETL/couchbase-tools/run_query.py \
    --endpoint $COUCHBASE_ENDPOINT \
    --username $COUCHBASE_USER \
    --password $COUCHBASE_PASSWORD \
    --file ETL/couchbase-tools/query_to_check_connection.n1ql
```

## Alternative: Run ETL via Docker Run

Instead of using `docker exec`, you can run a one-off container:

```bash
# From the Docker Compose project directory on the host
docker run --rm \
    --network compose_backend \
    -v /data/import:/import \
    -v $(pwd):/app \
    -w /app \
    --env-file .env \
    fastapi-app:latest \
    bash ETL/couchbase-tools/bootstrap_couchbase.sh /import
```

**Note:** The network name format is `<project-name>_<network-name>`. On the Naturalis server, the project name is `compose`, so the network is `compose_backend`.

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
- The `generate_and_sanitize_data.sh` script creates `filtered_*` and `reduced_*` files for handling large summaries

## Related Documentation

- [QUARTERLY_REBUILD_SOP.md](QUARTERLY_REBUILD_SOP.md) - Full quarterly rebuild procedure
- [WEEKLY_REBUILD_SOP.md](WEEKLY_REBUILD_SOP.md) - Weekly update procedure
- [REBUILD_DESIGN.md](REBUILD_DESIGN.md) - ETL pipeline design overview
- [couchbase-tools/README.md](couchbase-tools/README.md) - Couchbase tools documentation
