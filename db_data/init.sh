#!/usr/bin/env bash

#
# Couchbase initialization script
#
# This script is run the first time that the database is started
# It creates:
# - a cluster
# - a user
# - the buckets
# - the collections
# - the test data
# - the indexes
#

# Enables job control
set -m

# Enables error propagation
set -e

# Check if argument is set to drop the existing CouchBase cluster is true
if [ "$1" = true ] || [ "$1" = "true" ] ; then
  echo "Clearing existing CouchBase cluster..."
  rm -rf /opt/couchbase/var/*
fi


# Run the server and send it to the background
/entrypoint.sh couchbase-server &

# Check if couchbase server is up
check_db() {
  curl --silent http://127.0.0.1:8091/pools > /dev/null
  echo $?
}

# Variable used in echo
i=1
# Echo with
log() {
  echo "[$i] [$(date +"%T")] $@"
  i=`expr $i + 1`
}

# Wait until it's ready
until [[ $(check_db) = 0 ]]; do
  >&2 log "Waiting for Couchbase Server to be available ..."
  sleep 1
done

# Check if the cluster is already initialized
log "$(date +"%T") Reading cluster ........."
if couchbase-cli server-list -c 127.0.0.1 --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD | grep -q ERROR; then
    # Setup index and memory quota
    log "$(date +"%T") Init cluster ........."
    couchbase-cli cluster-init -c 127.0.0.1 --cluster-username $COUCHBASE_USER --cluster-password $COUCHBASE_PASSWORD \
    --cluster-name BPDP_DevCluster --cluster-ramsize 1024 --cluster-index-ramsize 1024 --services data,index,query \
    --index-storage-setting default

    # Create the buckets
    log "$(date +"%T") Create buckets ........."
    couchbase-cli bucket-create -c 127.0.0.1 --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --bucket BCDM \
        --bucket-type couchbase --bucket-ramsize 512
    couchbase-cli bucket-create -c 127.0.0.1 --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --bucket DERIVED \
        --bucket-type couchbase --bucket-ramsize 256
    couchbase-cli bucket-create -c 127.0.0.1 --username $COUCHBASE_USER --password $COUCHBASE_PASSWORD --bucket ANCILLARY \
        --bucket-type couchbase --bucket-ramsize 128

    # Create the collections
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket BCDM --create-collection _default.primary
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.accepted_terms
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.tax_geo_inst_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.country_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.institution_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.sequence_run_site_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.bin_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.dataset_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.primer_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --create-collection _default.taxonomy_summaries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.barcodeclusters
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.datasets
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.publications
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.countries
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.institutions
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.primers
    couchbase-cli collection-manage -c 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --create-collection _default.taxonomies

    # Insert data into the buckets
   log "$(date +"%T") Inserting data into buckets ........."
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket BCDM --scope-collection-exp _default.primary \
        --format lines --dataset file:///db_data/BCDM.jsonl --generate-key '%record_id%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.accepted_terms \
        --format lines --dataset file:///db_data/accepted_terms.jsonl --generate-key '%term%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.tax_geo_inst_summaries \
        --format lines --dataset file:///db_data/tax_geo_inst_summaries.jsonl --generate-key '%`tax_geo_inst_id`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.country_summaries \
        --format lines --dataset file:///db_data/country_summaries.jsonl --generate-key '%`country/ocean`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.institution_summaries \
        --format lines --dataset file:///db_data/institution_summaries.jsonl --generate-key '%`inst`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.sequence_run_site_summaries \
        --format lines --dataset file:///db_data/sequence_run_site_summaries.jsonl --generate-key '%`sequence_run_site`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.bin_summaries \
        --format lines --dataset file:///db_data/bin_summaries.jsonl --generate-key '%`bin_uri`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.dataset_summaries \
        --format lines --dataset file:///db_data/dataset_summaries.jsonl --generate-key '%`dataset.code`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.primer_summaries \
        --format lines --dataset file:///db_data/primer_summaries.jsonl --generate-key '%`name`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket DERIVED --scope-collection-exp _default.taxonomy_summaries \
        --format lines --dataset file:///db_data/taxonomy_summaries.jsonl --generate-key '%`taxid`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.barcodeclusters \
        --format lines --dataset file:///db_data/barcodeclusters.jsonl --generate-key '%`barcodecluster.uri`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.datasets \
        --format lines --dataset file:///db_data/datasets.jsonl --generate-key '%`dataset.code`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.countries \
        --format lines --dataset file:///db_data/geopols.jsonl --generate-key '%`name`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.institutions \
        --format lines --dataset file://db_data/institutions.jsonl --generate-key '%name%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.primers \
        --format lines --dataset file:///db_data/primers.jsonl --generate-key '%`name`%'
    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.taxonomies \
        --format lines --dataset file:///db_data/taxonomies.jsonl --generate-key '%`taxid`%'
#    cbimport json --cluster 127.0.0.1 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --bucket ANCILLARY --scope-collection-exp _default.publications \
#        --format lines --dataset file:///db_data/publications.jsonl --generate-key '%`publication.id`%'



    # Create user
#    log "$(date +"%T") Create users ........."
#    couchbase-cli user-manage -c 127.0.0.1:8091 -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD --set --rbac-username $COUCHBASE_USER --rbac-$COUCHBASE_PASSWORD $COUCHBASE_$COUCHBASE_PASSWORD \
#        --rbac-name "$COUCHBASE_USER" --roles admin --auth-domain local

    # Need to wait until query service is ready to process N1QL queries
    log "$(date +"%T") Waiting ........."
    sleep 20

    # Create indexes
    echo "$(date +"%T") Create indexes ........."
    cbq -u $COUCHBASE_USER -p $COUCHBASE_PASSWORD -f /db_data/indexes.validation.n1ql
fi

# Restores the server to the foreground
fg 1
