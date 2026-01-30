-- BUCKET: BCDM

DROP COLLECTION `BCDM`.`_default`.`primary` IF EXISTS;
CREATE COLLECTION `BCDM`.`_default`.`primary`;

-- BUCKET: DERIVED

DROP COLLECTION `DERIVED`.`_default`.`accepted_terms` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`tax_geo_inst_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`country_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`institution_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`sequence_run_site_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`bin_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`dataset_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`primer_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`taxonomy_summaries` IF EXISTS;
DROP COLLECTION `DERIVED`.`_default`.`specimen_ranks` IF EXISTS;

CREATE COLLECTION `DERIVED`.`_default`.`accepted_terms`;
CREATE COLLECTION `DERIVED`.`_default`.`tax_geo_inst_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`country_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`institution_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`sequence_run_site_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`bin_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`dataset_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`primer_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`taxonomy_summaries`;
CREATE COLLECTION `DERIVED`.`_default`.`specimen_ranks`;

-- BUCKET: ANCILLARY

DROP COLLECTION `ANCILLARY`.`_default`.`barcodeclusters` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`datasets` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`publications` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`countries` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`institutions` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`primers` IF EXISTS;
DROP COLLECTION `ANCILLARY`.`_default`.`taxonomies` IF EXISTS;

CREATE COLLECTION `ANCILLARY`.`_default`.`barcodeclusters`;
CREATE COLLECTION `ANCILLARY`.`_default`.`datasets`;
CREATE COLLECTION `ANCILLARY`.`_default`.`publications`;
CREATE COLLECTION `ANCILLARY`.`_default`.`countries`;
CREATE COLLECTION `ANCILLARY`.`_default`.`institutions`;
CREATE COLLECTION `ANCILLARY`.`_default`.`primers`;
CREATE COLLECTION `ANCILLARY`.`_default`.`taxonomies`;
