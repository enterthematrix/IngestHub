insert into ingestion_pattern (
  pattern_name,
  source,
  destination,
  create_timestamp
)
 values('Kafka_To_ADLS', 'KAFKA','ADLS', CURRENT_TIMESTAMP),
 ('Kafka_To_DeltaLake', 'KAFKA','DeltaLake', CURRENT_TIMESTAMP);

insert into job_template(
  sch_job_template_id,
  delete_after_completion,
  source_runtime_parameters,
  destination_runtime_parameters,
  source_connection_info,
  destination_connection_info,
  create_timestamp
  ) values (
    '73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{"KAFKA_TOPIC": "weather_refined", "KAFKA_CONSUMER_ADLS": "kafka_to_adls_consumer"}',
    '{}',
    '{"STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
    '{"STREAMSETS_ADLS_GEN2" : "0a1c97e9-9695-4931-ba8b-05fe3de39b47:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
    CURRENT_TIMESTAMP),
    (
    '838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa',
    false,
    '{"KAFKA_TOPIC": "[ "weather_refined" ]", "KAFKA_CONSUMER": "kafka_to_deltalake_consumer"}',
    '{"DeltaLake_Table": "hive_metastore.sanju.weather_events", "DeltaLake_Table_Location"="refined"}',
    '{"STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
    '{"STREAMSETS_DATABRICKS_DELTA_LAKE" : "a57fb112-8bf6-42da-ad1d-c1db19b245d5:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
    CURRENT_TIMESTAMP);


insert into ingestion_pattern_job_template_relationship (
  ingestion_pattern_id,
  job_template_id
) select p.ingestion_pattern_id, t.job_template_id
    from  ingestion_pattern p,
          job_template t
     where p.source =  'KAFKA'
     and p.destination = 'ADLS'
     and t.sch_job_template_id = '73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa';

insert into ingestion_pattern_job_template_relationship (
  ingestion_pattern_id,
  job_template_id
) select p.ingestion_pattern_id, t.job_template_id
    from  ingestion_pattern p,
          job_template t
     where p.source =  'KAFKA'
     and p.destination = 'DeltaLake'
     and t.sch_job_template_id = '838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa';