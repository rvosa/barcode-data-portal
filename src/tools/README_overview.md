# Tools

This directory contains utility scripts and tools that support the BOLD Public Portal application. These tools are primarily used for data processing, cache generation, testing, and administrative tasks.

## Overview

The tools in this directory serve several purposes:
- Testing database connections and performance
- Generating and managing cache data
- Processing data formats for export
- Creating visualizations like maps
- Supporting development and debugging tasks

## Tools

### Cache Generation Tools

- **generateSummaryCache.py**: Pre-generates cache data for common summary queries. Builds and stores cache data for efficient retrieval of summary information based on predefined triplet queries.

- **generateTaxMapCache.py**: Pre-generates cache data for taxonomy map visualizations. Processes taxonomy data to create hierarchical visualizations.

- **generateStatsCache.py**: Pre-generates cache data for general database statistics, such as total sequences, species counts, etc.

### Query Management Tools

- **generateQueryId.py**: Utility for generating query IDs from triplet query strings. Useful for testing and debugging query encoding/decoding.

- **generateReducedSummary.py**: Processes and reduces summary data to a more manageable format.

### Data Processing Tools

- **dataMapConverter.py**: Converts data between formats, specifically for transforming BOLD data model (BCDM) to Darwin Core (DwC) format. Used by the documents service for download capabilities.

### Visualization Tools

- **generateMap.py**: Creates map visualizations of collection locations. Takes coordinate data and renders points on a world map, with options for customization (size, color, opacity, etc.).

### Testing Tools

- **test_couchbase_connect.py**: Tests the connection to Couchbase and runs performance tests on different query types.

- **test_couchbase_download.py**: Tests downloading large amounts of data from Couchbase.

### Cache Query Lists

- **summary_cache_queries.json**: Contains predefined queries for generating summary cache data.
- **tax_map_cache_queries.json**: Contains predefined queries for generating taxonomy map cache data.

## Usage in Architecture

These tools integrate with the BOLD Portal architecture in several ways:

### Service Integration

- The map generation tool is called by the **maps** service to create visualizations.
- The data converter is used by the **documents** service to handle format conversions for downloads.
- The cache generation tools are used to pre-populate caches that the services rely on for performance.

### Caching Strategy

Many of these tools support the application's caching strategy:
1. Pre-generate cache data for common queries (summary, taxonomy, statistics)
2. Use Redis and file-based caching to store results
3. Allow services to quickly retrieve cached data instead of performing expensive database operations

### Performance Optimization

- By pre-generating cache for common queries, the tools help optimize application performance.
- The testing tools help identify and address potential performance bottlenecks.

### Development and Maintenance

- These tools facilitate development, testing, and maintenance tasks.
- They can be run independently of the main application for tasks like cache warming, data export, or diagnostics.

## Running the Tools

Most tools follow a similar command-line interface pattern:

```bash
# Generate summary cache
python generateSummaryCache.py -i summary_cache_queries.json

# Generate taxonomy map cache
python generateTaxMapCache.py -i tax_map_cache_queries.json

# Generate statistics cache
python generateStatsCache.py

# Generate a query ID
python generateQueryId.py -t "tax:species:Homo sapiens" -e "limited"

# Convert data format
python dataMapConverter.py -i input.json -o output.json -m mapping.tsv

# Test Couchbase connection
python test_couchbase_connect.py

# Generate a map
python generateMap.py input_map.png output_map.png --sizefactor 0.5 --alpha 180
```

## Related Components

- **dao.py**: The tools interact with the Data Access Object for database operations.
- **util.py**: Provides utility functions for caching, query processing, and more.
- **services/**: The services that use the cached data and functionality from these tools.