-- BUCKET: BCDM

DROP COLLECTION `BCDM`.`_default`.`primary`;
CREATE COLLECTION `BCDM`.`_default`.`primary`;

-- BUCKET: DERIVED

DROP COLLECTION `DERIVED`.`_default`.`accepted_terms`;
DROP COLLECTION `DERIVED`.`_default`.`tax_geo_inst_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`country_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`institution_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`sequence_run_site_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`bin_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`dataset_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`primer_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`taxonomy_summaries`;
DROP COLLECTION `DERIVED`.`_default`.`specimen_ranks`;

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

DROP COLLECTION `ANCILLARY`.`_default`.`barcodeclusters`;
DROP COLLECTION `ANCILLARY`.`_default`.`datasets`;
DROP COLLECTION `ANCILLARY`.`_default`.`publications`;
DROP COLLECTION `ANCILLARY`.`_default`.`countries`;
DROP COLLECTION `ANCILLARY`.`_default`.`institutions`;
DROP COLLECTION `ANCILLARY`.`_default`.`primers`;
DROP COLLECTION `ANCILLARY`.`_default`.`taxonomies`;

CREATE COLLECTION `ANCILLARY`.`_default`.`barcodeclusters`;
CREATE COLLECTION `ANCILLARY`.`_default`.`datasets`;
CREATE COLLECTION `ANCILLARY`.`_default`.`publications`;
CREATE COLLECTION `ANCILLARY`.`_default`.`countries`;
CREATE COLLECTION `ANCILLARY`.`_default`.`institutions`;
CREATE COLLECTION `ANCILLARY`.`_default`.`primers`;
CREATE COLLECTION `ANCILLARY`.`_default`.`taxonomies`;
