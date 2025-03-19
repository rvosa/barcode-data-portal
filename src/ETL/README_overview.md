# ETL

This directory contains the Extract, Transform, Load (ETL) scripts for the BOLD Public Portal. These scripts are responsible for extracting data from BOLD's internal database, transforming it into a standardized format, and loading it into the portal's Couchbase database.

## Overview

The ETL process is a critical part of the BOLD Public Portal architecture, handling the transformation of raw data from the BOLD system's PostgreSQL database into optimized documents for the Couchbase-based public API. This process generates:

1. Primary data documents (BCDM - BOLD Core Data Model)
2. Summary/aggregation documents for efficient querying
3. Term index documents for search functionality

## Data Flow from PostgreSQL to Couchbase

The ETL pipeline follows this specific flow:

1. **Extraction**: Data is extracted from the BOLD Data Submission Workbench PostgreSQL database using SQL queries against the `singlepane_view` (defined in `database_singlepane_view.sql`).

2. **Transformation**: 
   - Raw PostgreSQL records are transformed into standardized BCDM format.
   - Data policies are applied (filtering protected or embargoed data).
   - Summary documents are generated for taxonomic, geographic, and other dimensions.
   - Terms are extracted and indexed for search functionality.

3. **Loading**:
   - Primary BCDM documents are loaded into Couchbase collections.
   - Summary documents are loaded into dedicated collections.
   - Term indexes are loaded into search-optimized collections.

4. **Validation**:
   - Post-load validation ensures data integrity.
   - Consistency checks verify relationships between documents.

## ETL and Caching Integration

The ETL process integrates with the caching strategy in several key ways:

1. **Pre-computed Summary Documents**:
   - ETL scripts generate summary documents that are stored directly in Couchbase.
   - These summaries provide pre-aggregated data for common dimensions (taxonomy, geography, institutions, etc.).
   - The summary documents serve as a persistent cache layer, eliminating the need for expensive aggregation queries at runtime.

2. **Cache Warming**:
   - After ETL completes, cache warming scripts (in the `tools/` directory) are executed.
   - These scripts generate cached results for common queries and store them in Redis.
   - Pre-populating Redis with frequently accessed data improves initial response times.

3. **Cache Invalidation**:
   - ETL job completion triggers cache invalidation for affected data.
   - Redis cache entries that depend on updated data are cleared.
   - New cache entries are generated for updated data.

4. **Static Data for Client Caching**:
   - ETL generates certain static files (e.g., taxonomy trees, geographic boundaries) that are served as cacheable assets.
   - These files include appropriate cache-control headers for client-side caching.

## Pipelines

The ETL system has two main pipelines, documented in the markdown files:

- **Weekly Update Pipeline** (`WEEKLY_REBUILD_SOP.md`): Incremental updates of data
- **Quarterly Bootstrap Pipeline** (`QUARTERLY_REBUILD_SOP.md`): Full rebuild of the database

The pipelines are also visually represented in the PNG files (`Weekly_Update_Pipeline.png` and `Quarterly_Bootstrap_Pipeline.png`).

## ETL Schedule and Triggers

ETL jobs are run on a defined schedule with specific triggers:

### Weekly Update Pipeline
- **Schedule**: Runs every Sunday at 00:00 UTC
- **Trigger Mechanism**: Automated cron job on the ETL server
- **Duration**: Typically completes within 2-4 hours
- **Scope**: Processes only new or modified records since the last run
- **Notification**: Emails ETL completion status to the administration team

### Quarterly Bootstrap Pipeline
- **Schedule**: Runs on the first day of January, April, July, and October
- **Trigger Mechanism**: Automated cron job with manual confirmation
- **Duration**: Typically takes 24-48 hours to complete
- **Scope**: Complete rebuild of all collections from source PostgreSQL data
- **Notification**: Sends progress updates and completion notification to the administration team

### Manual Triggers
- ETL jobs can also be triggered manually via the administration interface
- Emergency updates can be scheduled outside the regular cadence when critical data fixes are needed

## Testing ETL Changes

Before deploying changes to the ETL pipeline in production, the following testing process is followed:

1. **Development Testing**:
   - ETL changes are first tested against a development PostgreSQL database.
   - Output documents are validated for schema compliance and data integrity.
   - Unit tests verify specific transformation logic.

2. **Staging Environment**:
   - A complete ETL run is performed on the staging environment.
   - This uses a copy or subset of production data.
   - Staging Couchbase is populated with the results.

3. **Validation Testing**:
   - Automated tests compare record counts, key metrics, and statistical distributions between staging and production.
   - Sample record validation ensures data quality.
   - API tests verify that services work correctly with the transformed data.

4. **Performance Testing**:
   - ETL execution time is measured and compared to baseline.
   - Resource usage (memory, CPU, disk I/O) is monitored.
   - Database performance tests ensure query performance meets requirements.

5. **Rollback Plan**:
   - Each ETL deployment includes a rollback plan.
   - Couchbase snapshots are created before running production ETL.
   - Previous Couchbase state can be restored if issues are detected.

## Main Components

### Data Extraction

- `export_singlepane_view.py`: Exports data from the PostgreSQL database's singlepane view
- `extract_bold4_singlepane_to_BCDM.py`: Transforms the raw database records into the standardized BCDM format
- `database_singlepane_view.sql`: SQL definition for the database view used for extraction

### Data Transformation and Summarization

These scripts generate various summary documents that allow for efficient querying and visualization:

- `extract_terms_and_summary_from_BCDM.py`: Extracts searchable terms and summary data
- `extract_minimized_terms_with_inst_bins_ids_codes_BCDM.py`: Extracts additional terms for search functionality
- `extract_bin_summary.py`: Generates summaries for BINs (Barcode Index Numbers)
- `extract_country_summary.py`: Generates country/geographic summaries
- `extract_dataset_summary.py`: Generates dataset summaries
- `extract_institution_summary.py`: Generates institution summaries
- `extract_primer_summary.py`: Generates primer summaries
- `extract_sequence_run_site_summary.py`: Generates summaries for sequencing sites
- `extract_taxonomy_summary.py`: Generates taxonomy summaries

### Data Filtering and Processing

- `apply_BCDM_policies.sh`: Shell script for applying data policies to BCDM documents
- `filter_barcodeclusters_based_on_bcdm.py`: Filters barcode cluster data based on BCDM content
- `generate_and_sanitize_data.sh`: Main orchestration script for the ETL process

### Subfolders

- `couchbase-tools/`: Contains tools specific to Couchbase data operations
- `postprocess/`: Contains scripts for post-processing data after the main ETL operations

## Key Concepts

### BCDM (BOLD Core Data Model)

The central data structure used throughout the ETL process and the application. This is a standardized document format that represents specimens, sequences, and associated metadata in a consistent way.

### Summaries

The summary documents are pre-aggregated views of the primary data, organized by different dimensions (geographic, taxonomic, institutional, etc.). These summaries power the web interface dashboards and visualizations and enable efficient querying of the API.

### Terms

The terms extracted during the ETL process form the basis of the search functionality. These are indexed in Couchbase to allow quick lookup of specimens, sequences, and other data based on various criteria.

## Integration with Overall Architecture

The ETL scripts interact with the rest of the application in several ways:

1. **Data Source**: They connect to the primary BOLD PostgreSQL database to extract source data.
2. **Data Destination**: They generate documents that are loaded into the Couchbase database.
3. **Data Structure**: They define the document structure that the `dao.py` module uses to query data.
4. **Cache Preparation**: Some scripts generate pre-computed query results that are stored in Redis for performance.

The output of these ETL processes powers the entire public portal:
- The services retrieve data via the DAO layer
- The views present this data to users
- The search functionality relies on the extracted terms

## Usage

The main ETL process is orchestrated through the `generate_and_sanitize_data.sh` script, which:

1. Applies data policies to raw BCDM documents
2. Generates summary and terms documents
3. Creates specialized summaries for different data dimensions
4. Sanitizes registry documents

## Related Components

- **dao.py**: Data Access Object that queries the ETL-generated documents
- **services/**: API services that use the DAO to retrieve data
- **tools/**: Contains utility scripts used by the ETL process