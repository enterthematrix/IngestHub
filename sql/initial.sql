INSERT INTO ingestion_pattern (pattern_name, source, destination, create_timestamp)
VALUES
('Kafka_To_ADLS', 'KAFKA', 'ADLS', CURRENT_TIMESTAMP),
('Kafka_To_DeltaLake', 'KAFKA', 'DeltaLake', CURRENT_TIMESTAMP),
('Kafka_To_Snowflake', 'KAFKA', 'Snowflake', CURRENT_TIMESTAMP),
('FS_To_Snowflake', 'FS/NFS', 'Snowflake', CURRENT_TIMESTAMP);

INSERT INTO job_template (sch_job_template_id, delete_after_completion, source_runtime_parameters, destination_runtime_parameters, source_connection_info, destination_connection_info, create_timestamp)
VALUES
('73bf3338-e52c-492b-ac68-7e0e572a6ae2:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"KAFKA_TOPIC":"weather_refined", "KAFKA_CONSUMER_ADLS":"kafka_to_adls_consumer"}',
'{}',
'{"STREAMSETS_KAFKA":"9c07ac94-c7fe-4cff-9ff5-1b19dcfb7b37:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
'{"STREAMSETS_ADLS_GEN2" : "4a0072f2-c66e-4f2e-b213-ce583713076b:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('838b7cbc-68c4-44ba-bf2c-d856d95f5467:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"KAFKA_TOPIC": "[\n\"weather_refined\"\n]"}',
'{"DeltaLake_Table": "hive_metastore.sanju.weather_events", "DeltaLake_Table_Location": "refined"}',
'{"STREAMSETS_KAFKA" : "9c07ac94-c7fe-4cff-9ff5-1b19dcfb7b37:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
'{"STREAMSETS_DATABRICKS_DELTA_LAKE" : "625b1d48-4e95-4250-93e8-439b419a5892:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('fac8dee1-cff7-46a8-991c-746fc7705fc6:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"REFINED_KAFKA_TOPIC": "weather_refined", "KAFKA_CONSUMER_GROUP": "cg_weather_snowflake_123451"}',
'{"SNOWFLAKE_WAREHOUSE": "STREAMSETSSES_WH", "SNOWFLAKE_DB": "STREAMSETSSES_DB", "SNOWFLAKE_SCHEMA": "SANJU", "SNOWFLAKE_TABLE": "weather_events"}',
'{"STREAMSETS_KAFKA" : "9c07ac94-c7fe-4cff-9ff5-1b19dcfb7b37:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
'{"STREAMSETS_SNOWFLAKE" : "bf13152c-66a9-4d4f-8acf-17a484ddc98e:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('1acddc7e-06c2-4871-baae-3f55cec47be4:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
'{"SNOWFLAKE_TABLE_NAME": "FLIGHTS"}',
'{}',
'{"STREAMSETS_SNOWFLAKE" : "bf13152c-66a9-4d4f-8acf-17a484ddc98e:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP);

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'KAFKA' AND p.destination = 'ADLS'
AND t.sch_job_template_id = '73bf3338-e52c-492b-ac68-7e0e572a6ae2:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'KAFKA' AND p.destination = 'DeltaLake'
AND t.sch_job_template_id = '838b7cbc-68c4-44ba-bf2c-d856d95f5467:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'KAFKA' AND p.destination = 'Snowflake'
AND t.sch_job_template_id = 'fac8dee1-cff7-46a8-991c-746fc7705fc6:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'FS/NFS' AND p.destination = 'Snowflake'
AND t.sch_job_template_id = '1acddc7e-06c2-4871-baae-3f55cec47be4:241d5ea9-f21d-11eb-a19e-07108e36db4e';
