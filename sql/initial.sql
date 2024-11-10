INSERT INTO ingestion_pattern (pattern_name, source, destination, create_timestamp)
VALUES
('FS_To_ADLS', 'FS/NFS', 'ADLS', CURRENT_TIMESTAMP),
('FS_To_DeltaLake', 'FS/NFS', 'DeltaLake', CURRENT_TIMESTAMP),
('FS_To_Snowflake', 'FS/NFS', 'Snowflake', CURRENT_TIMESTAMP),
('FS_To_MySQL', 'FS/NFS', 'MySQL', CURRENT_TIMESTAMP);

INSERT INTO job_template (sch_job_template_id, delete_after_completion, source_runtime_parameters, destination_runtime_parameters, source_connection_info, destination_connection_info, create_timestamp)
VALUES
('f3cd513b-d394-47d4-a011-6ee65d66fc1b:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
'{"DeltaLake_Table": "sanju.flights", "DeltaLake_Table_Location": "flights", "DeltaLake_Stage_File_Prefix": "flight" }',
'{}',
'{"STREAMSETS_DATABRICKS_DELTA_LAKE" : "625b1d48-4e95-4250-93e8-439b419a5892:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('464804d7-987c-4176-b66c-1834bf3f95c9:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
'{"ADLS_FILE_PREFIX": "flights"}',
'{}',
'{"STREAMSETS_ADLS_GEN2" : "4a0072f2-c66e-4f2e-b213-ce583713076b:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('1acddc7e-06c2-4871-baae-3f55cec47be4:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
'{"SNOWFLAKE_TABLE_NAME": "FLIGHTS"}',
'{}',
'{"STREAMSETS_SNOWFLAKE" : "bf13152c-66a9-4d4f-8acf-17a484ddc98e:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP),
('e189b61f-6721-4c66-a63b-7de45970f34f:241d5ea9-f21d-11eb-a19e-07108e36db4e', false,
'{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
'{"MySQL_TABLE_NAME": "flights", "MySQL_TABLE_SCHEMA": "sanju"}',
'{}',
'{"JDBC" : "7200fe5b-93d8-405f-b1ff-3ac1276120bf:241d5ea9-f21d-11eb-a19e-07108e36db4e"}',
CURRENT_TIMESTAMP);

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'FS/NFS' AND p.destination = 'DeltaLake'
AND t.sch_job_template_id = 'f3cd513b-d394-47d4-a011-6ee65d66fc1b:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'FS/NFS' AND p.destination = 'ADLS'
AND t.sch_job_template_id = '464804d7-987c-4176-b66c-1834bf3f95c9:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'FS/NFS' AND p.destination = 'Snowflake'
AND t.sch_job_template_id = '1acddc7e-06c2-4871-baae-3f55cec47be4:241d5ea9-f21d-11eb-a19e-07108e36db4e';

INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
SELECT p.ingestion_pattern_id, t.job_template_id
FROM ingestion_pattern p, job_template t
WHERE p.source = 'FS/NFS' AND p.destination = 'MySQL'
AND t.sch_job_template_id = 'e189b61f-6721-4c66-a63b-7de45970f34f:241d5ea9-f21d-11eb-a19e-07108e36db4e';
