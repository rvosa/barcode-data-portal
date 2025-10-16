#!/bin/bash

# Requires:
# python
# BCDM: bold_singlepane_public_export.jsonl
# Summaries: tax_geo_inst_summaries.jsonl, country_summaries.jsonl. institution_summaries.jsonl
#            sequence_run_site_summaries.jsonl, bin_summaries.jsonl, dataset_summaries.jsonl
#            primer_summaries.jsonl, taxonomy_summaries.jsonl
# Terms: accepted_terms_combined.jsonl
# Registries: bold_dataset_registry.jsonl, bold_barcodecluster_registry.jsonl, bold_geopol_registry.jsonl
#             bold_institution_registry.jsonl, bold_primer_registry.jsonl, bold_taxonomy_registry.jsonl

printf "Step 1: Drop and recreate collections\n"
python ETL/couchbase-tools/run_query.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file ETL/couchbase-tools/couchbase_collections.sql
printf "\n"

printf "Step 2: Load primary documents\n"
python ETL/couchbase-tools/bulk_load_documents.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'record_id' --file $IMPORT_DIR/bold_singlepane_public_export.jsonl
printf "\n"

printf "Step 3: Load summary and terms\n"
printf "Load summary and terms documents\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection tax_geo_inst_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'tax_geo_inst_id' --file $IMPORT_DIR/tax_geo_inst_summaries.jsonl
printf "\nLoad country summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection country_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'country/ocean' --file $IMPORT_DIR/country_summaries.jsonl
printf "\nLoad institution summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection institution_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'inst' --file $IMPORT_DIR/institution_summaries.jsonl
printf "\nLoad sequence run site summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection sequence_run_site_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'sequence_run_site' --file $IMPORT_DIR/sequence_run_site_summaries.jsonl
printf "\nLoad bin summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection bin_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'bin_uri' --file $IMPORT_DIR/bin_summaries.jsonl
printf "\nLoad dataset summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection dataset_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $IMPORT_DIR/dataset_summaries.jsonl
printf "\nLoad primer summary\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection primer_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $IMPORT_DIR/primer_summaries.jsonl
printf "\nLoad special summaries that use registries\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection taxonomy_summaries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $IMPORT_DIR/taxonomy_summaries.jsonl
printf "\nLoad accepted terms\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket DERIVED --collection accepted_terms --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'term' --file $IMPORT_DIR/accepted_terms_combined.jsonl
printf "\n"

printf "Step 4: Load ancillary documents\n"
printf "Load dataset registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection datasets --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'dataset.code' --file $IMPORT_DIR/bold_dataset_registry.jsonl
printf "\nLoad barcode cluster registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection barcodeclusters --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'barcodecluster.uri' --file $IMPORT_DIR/bold_barcodecluster_registry.jsonl
printf "\nLoad geopol registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection countries --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $IMPORT_DIR/bold_geopol_registry.jsonl
printf "\nLoad institution registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection institutions --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $IMPORT_DIR/bold_institution_registry.jsonl
printf "\nLoad primer registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection primers --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'name' --file $IMPORT_DIR/bold_primer_registry.jsonl
printf "\nLoad taxonomy registry\n"
python ETL/couchbase-tools/bulk_load_documents.py --bucket ANCILLARY --collection taxonomies --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --primary-key 'taxid' --file $IMPORT_DIR/bold_taxonomy_registry.jsonl

printf "Step 5: Generate indexes\n"
python ETL/couchbase-tools/run_query.py --endpoint $COUCHBASE_ENDPOINT --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --file ETL/couchbase-tools/couchbase_index_definitions.sql
