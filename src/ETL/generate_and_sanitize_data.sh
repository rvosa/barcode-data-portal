#!/bin/bash

# Requires:
# python, jq, iconv
# BCDM: bold_singlepane_public_export.jsonl
# Registries: bold_dataset_registry.jsonl, bold_barcodecluster_registry.jsonl, bold_geopol_registry.jsonl
#             bold_institution_registry.jsonl, bold_primer_registry.jsonl, bold_taxonomy_registry.jsonl

SIZE_LIMIT=20000000

printf "Step 1: Download registry documents\n"
git clone --quiet "https:///oauth2:$IMPORT_REGISTRY_TOKEN@gitlab.com/naturalis/bii/bge/barcode-data-portal-registry-files.git" $IMPORT_DIR/registry_files
cd $IMPORT_DIR/registry_files && for file in *.gz; do gunzip -f "$file" -c > "../${file%.gz}"; done && cd - > /dev/null 2>&1
rm -rf $IMPORT_DIR/registry_files

printf "Step 2: Strip null values from the source file\n"
cat $IMPORT_DIR/bold_singlepane_public_export.jsonl | jq -c "del(..|nulls)" > $IMPORT_DIR/bold_singlepane_public_export_null_filtered.jsonl

printf "Step 3: Apply policies to BCDM documents\n"
cat $IMPORT_DIR//bold_singlepane_public_export_null_filtered.jsonl | bash ETL/apply_BCDM_policies.sh > $IMPORT_DIR/bold_singlepane_public_export_filtered.jsonl
mv $IMPORT_DIR/bold_singlepane_public_export_filtered.jsonl $IMPORT_DIR/bold_singlepane_public_export.jsonl

printf "Step 4: Generate summary and terms documents\n"
python ETL/extract_terms_and_summary_from_BCDM.py --summary_file $IMPORT_DIR/tax_geo_inst_summaries.jsonl --terms_file $IMPORT_DIR/accepted_terms.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl
python ETL/extract_minimized_terms_with_inst_bins_ids_codes_BCDM.py --terms_file $IMPORT_DIR/accepted_terms_contd.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl
cat $IMPORT_DIR/accepted_terms.jsonl $IMPORT_DIR/accepted_terms_contd.jsonl | jq -c 'select(.term != "" and .term != null)' > $IMPORT_DIR/accepted_terms_combined.jsonl
rm $IMPORT_DIR/accepted_terms.jsonl $IMPORT_DIR/accepted_terms_contd.jsonl

printf "Step 4.1 Generate country summary\n"
python ETL/extract_country_summary.py --summary_file $IMPORT_DIR/country_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

touch $IMPORT_DIR/reduced_country_summaries.jsonl $IMPORT_DIR/filtered_country_summaries.jsonl
while IFS= read -r country; do
    file_name="country_$(echo "$country" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"country\/ocean\":\"$country\"" $IMPORT_DIR/country_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id=$(python tools/generateQueryId.py -t "geo:country/ocean:$country" -e "full")
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_country_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_country_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/country_summaries.jsonl | jq -r '."country/ocean"')

printf "Step 4.2 Generate institution summary\n"
python ETL/extract_institution_summary.py --summary_file $IMPORT_DIR/institution_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

touch $IMPORT_DIR/reduced_institution_summaries.jsonl $IMPORT_DIR/filtered_institution_summaries.jsonl
while IFS= read -r inst; do
    file_name="inst_$(echo "$inst" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"inst\":\"$inst\"" $IMPORT_DIR/institution_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id=$(python tools/generateQueryId.py -t "inst:name:$inst" -e "full")
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_institution_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_institution_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/institution_summaries.jsonl | jq -r '.inst')

printf "Step 4.3 Generate sequence run site summary\n"
python ETL/extract_sequence_run_site_summary.py --summary_file $IMPORT_DIR/sequence_run_site_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

touch $IMPORT_DIR/reduced_sequence_run_site_summaries.jsonl $IMPORT_DIR/filtered_sequence_run_site_summaries.jsonl
while IFS= read -r seq_run_site; do
    file_name="seq_run_site_$(echo "$seq_run_site" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"sequence_run_site\":\"$seq_run_site\"" $IMPORT_DIR/sequence_run_site_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id=$(python tools/generateQueryId.py -t "inst:seqsite:$seq_run_site" -e "full")
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_sequence_run_site_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_sequence_run_site_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/sequence_run_site_summaries.jsonl | jq -r '.sequence_run_site')

printf "Step 4.4 Generate bin summary\n"
python ETL/extract_bin_summary.py < $IMPORT_DIR/bold_singlepane_public_export.jsonl > $IMPORT_DIR/bin_summaries_raw.jsonl
cat $IMPORT_DIR/bin_summaries_raw.jsonl | jq -R "fromjson? | . " -c > $IMPORT_DIR/bin_summaries_cleaned.jsonl
jq -c 'sort_by(.counts.sequences) | reverse | .[0:2000] | .[]' $IMPORT_DIR/bin_summaries_cleaned.jsonl > $IMPORT_DIR/bin_summaries.jsonl
rm $IMPORT_DIR/bin_summaries_raw.jsonl

touch $IMPORT_DIR/reduced_bin_summaries.jsonl $IMPORT_DIR/filtered_bin_summaries.jsonl
while IFS= read -r bin; do
    file_name="bin_$(echo "$bin" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"bin_uri\":\"$bin\"" $IMPORT_DIR/bin_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id=$(python tools/generateQueryId.py -t "bin:uri:$bin" -e "full")
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_bin_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_bin_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/bin_summaries.jsonl | jq -r '.bin_uri')

printf "Step 4.5 Generate dataset summary\n"
python ETL/extract_dataset_summary.py --summary_file $IMPORT_DIR/dataset_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

touch $IMPORT_DIR/reduced_dataset_summaries.jsonl $IMPORT_DIR/filtered_dataset_summaries.jsonl
while IFS= read -r dataset; do
    file_name="dataset_$(echo "$dataset" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"dataset.code\":\"$dataset\"" $IMPORT_DIR/dataset_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id=$(python tools/generateQueryId.py -t ""recordsetcode:code:$dataset"" -e "full")
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_dataset_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_dataset_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/dataset_summaries.jsonl | jq -r '."dataset.code"')

printf "Step 4.6 Generate primer summary\n"
python ETL/extract_primer_summary.py --summary_file $IMPORT_DIR/primer_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

touch $IMPORT_DIR/reduced_primer_summaries.jsonl $IMPORT_DIR/filtered_primer_summaries.jsonl
while IFS= read -r primer; do
    file_name="primer_$(echo "$primer" | sed -r 's/[^a-zA-Z0-9]+/-/g').json"
    grep -F "\"name\":\"$primer\"" $IMPORT_DIR/primer_summaries.jsonl > $IMPORT_DIR/$file_name

    query_id="null"
    reduced_summary=$(cat $IMPORT_DIR/$file_name | python tools/generateReducedSummary.py)
    printf "$query_id\t$reduced_summary\n" >> $IMPORT_DIR/reduced_primer_summaries.jsonl

    jq -c ".aggregates = {}" $IMPORT_DIR/$file_name >> $IMPORT_DIR/filtered_primer_summaries.jsonl
done < <(awk -v size_limit="$SIZE_LIMIT" '{ if (length($0) > size_limit) print }' $IMPORT_DIR/primer_summaries.jsonl | jq -r '.name')

printf "Step 4.7 Generate specimen rank summary\n"
python ETL/extract_rank_summary.py --output_file $IMPORT_DIR/specimen_ranks.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl

printf "Step 5: Sanitize registry documents\n"
jq -c '. | select(.name != "")' $IMPORT_DIR/bold_institution_registry.jsonl > $IMPORT_DIR/bold_institution_registry_filtered.jsonl
mv $IMPORT_DIR/bold_institution_registry_filtered.jsonl $IMPORT_DIR/bold_institution_registry.jsonl

# Handling utf-8 encoding
iconv -f 'iso-8859-1' -t UTF-8 $IMPORT_DIR/bold_institution_registry.jsonl > $IMPORT_DIR/bold_institution_registry.utf8.jsonl
mv $IMPORT_DIR/bold_institution_registry.utf8.jsonl $IMPORT_DIR/bold_institution_registry.jsonl
iconv -f 'iso-8859-1' -t UTF-8 $IMPORT_DIR/bold_taxonomy_registry.jsonl > $IMPORT_DIR/bold_taxonomy_registry.utf8.jsonl
mv $IMPORT_DIR/bold_taxonomy_registry.utf8.jsonl $IMPORT_DIR/bold_taxonomy_registry.jsonl

printf "Step 6: Generate special summaries that use registries\n"
python ETL/extract_taxonomy_summary.py --registry_file $IMPORT_DIR/bold_taxonomy_registry.jsonl --summary_file $IMPORT_DIR/taxonomy_summaries.jsonl < $IMPORT_DIR/bold_singlepane_public_export.jsonl
