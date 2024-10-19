DROP TABLE users;

DROP TABLE ingestion_pattern;

DROP TABLE job_template;

DROP TABLE ingestion_pattern_job_template_relationship;

DROP TABLE job_instance;

--INSERT SAMPLE DATA
DELETE FROM ingestion_pattern;

INSERT INTO ingestion_pattern
            (pattern_name,
             source,
             destination,
             create_timestamp)
VALUES     ('Kafka_To_ADLS',
            'KAFKA',
            'ADLS',
            CURRENT_TIMESTAMP),
            ('Kafka_To_DeltaLake',
             'KAFKA',
             'DeltaLake',
             CURRENT_TIMESTAMP),
            ('Kafka_To_Snowflake',
             'KAFKA',
             'Snowflake',
             CURRENT_TIMESTAMP),
            ('FS_To_Snowflake',
             'FS/NFS',
             'Snowflake',
             CURRENT_TIMESTAMP);


DELETE FROM job_template;

INSERT INTO job_template
            (sch_job_template_id,
             delete_after_completion,
             source_runtime_parameters,
             destination_runtime_parameters,
             source_connection_info,
             destination_connection_info,
             create_timestamp)
VALUES(
    '73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{
    "KAFKA_TOPIC":"weather_refined",
    "KAFKA_CONSUMER_ADLS":"kafka_to_adls_consumer"
    }',
    '{}',
    '{
    "STREAMSETS_KAFKA":"24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    '{
    "STREAMSETS_ADLS_GEN2" : "0a1c97e9-9695-4931-ba8b-05fe3de39b47:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    CURRENT_TIMESTAMP),
    (
    '838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{
    "KAFKA_TOPIC": "[\n\"weather_refined\"\n]",
    "KAFKA_CONSUMER": "kafka_to_deltalake_consumer"
    }',
    '{
    "DeltaLake_Table": "hive_metastore.sanju.weather_events",
    "DeltaLake_Table_Location": "refined"
    }',
    '{
    "STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    '{
    "STREAMSETS_DATABRICKS_DELTA_LAKE" : "a57fb112-8bf6-42da-ad1d-c1db19b245d5:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    CURRENT_TIMESTAMP),
    (
    'fac8dee1-cff7-46a8-991c-746fc7705fc6:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{
    "REFINED_KAFKA_TOPIC": "weather_refined",
    "KAFKA_CONSUMER_GROUP": "cg_weather_snowflake_123451"
    }',
    '{
    "SNOWFLAKE_WAREHOUSE": "STREAMSETSSES_WH",
    "SNOWFLAKE_DB": "STREAMSETSSES_DB",
    "SNOWFLAKE_SCHEMA": "SANJU",
    "SNOWFLAKE_TABLE": "weather_events"
    }',
    '{
    "STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    '{
    "STREAMSETS_SNOWFLAKE" : "0d43814f-98cd-4e65-875e-c84b0154d30f:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    CURRENT_TIMESTAMP),
    (
    '1acddc7e-06c2-4871-baae-3f55cec47be4:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{
		"BatchSize": "5000",
		"Dir": "/flight_data",
		"Filename_Pattern": "sample_10k.csv.bz2"
	}',
    '{
		"SNOWFLAKE_TABLE_NAME": "FLIGHTS"
	}',
    '{}',
    '{
    "STREAMSETS_SNOWFLAKE" : "0d43814f-98cd-4e65-875e-c84b0154d30f:cd4694f6-2c60-11ec-988d-5b2e605d28aa"
    }',
    CURRENT_TIMESTAMP);


DELETE FROM ingestion_pattern_job_template_relationship;

INSERT INTO ingestion_pattern_job_template_relationship
            (ingestion_pattern_id,
             job_template_id)
SELECT p.ingestion_pattern_id,
       t.job_template_id
FROM   ingestion_pattern p,
       job_template t
WHERE  p.source = 'KAFKA'
       AND p.destination = 'ADLS'
       AND t.sch_job_template_id =
'73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa';

INSERT INTO ingestion_pattern_job_template_relationship
            (ingestion_pattern_id,
             job_template_id)
SELECT p.ingestion_pattern_id,
       t.job_template_id
FROM   ingestion_pattern p,
       job_template t
WHERE  p.source = 'KAFKA'
       AND p.destination = 'DeltaLake'
       AND t.sch_job_template_id =
'838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa';

INSERT INTO ingestion_pattern_job_template_relationship
            (ingestion_pattern_id,
             job_template_id)
SELECT p.ingestion_pattern_id,
       t.job_template_id
FROM   ingestion_pattern p,
       job_template t
WHERE  p.source = 'KAFKA'
       AND p.destination = 'Snowflake'
       AND t.sch_job_template_id =
'fac8dee1-cff7-46a8-991c-746fc7705fc6:cd4694f6-2c60-11ec-988d-5b2e605d28aa';

INSERT INTO ingestion_pattern_job_template_relationship
            (ingestion_pattern_id,
             job_template_id)
SELECT p.ingestion_pattern_id,
       t.job_template_id
FROM   ingestion_pattern p,
       job_template t
WHERE  p.source = 'FS/NFS'
       AND p.destination = 'Snowflake'
       AND t.sch_job_template_id =
'1acddc7e-06c2-4871-baae-3f55cec47be4:cd4694f6-2c60-11ec-988d-5b2e605d28aa';