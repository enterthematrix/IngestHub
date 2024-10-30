import os
from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, TIMESTAMP, Boolean, ForeignKey, JSON, text

from ingesthub_logger import Logger


# Database and Flask Configuration as a separate class
class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URI','sqlite:///streamsets.db')


# Flask App Class
class DatabaseManager:
    def __init__(self):
        self.logger = Logger()
        self.app = Flask(__name__)
        self.app.config.from_object(Config)
        self.db = self.init_db()

    def init_db(self):
        db = SQLAlchemy(model_class=Base)
        db.init_app(self.app)
        return db

    def create_tables(self):
        with self.app.app_context():
            self.db.create_all()

    def load_templates(self):
        with self.app.app_context():
            # Sample SQL statements to execute
            template_sql = [
                """
                INSERT INTO ingestion_pattern (pattern_name, source, destination, create_timestamp)
                VALUES
                ('Kafka_To_ADLS', 'KAFKA', 'ADLS', CURRENT_TIMESTAMP),
                ('Kafka_To_DeltaLake', 'KAFKA', 'DeltaLake', CURRENT_TIMESTAMP),
                ('Kafka_To_Snowflake', 'KAFKA', 'Snowflake', CURRENT_TIMESTAMP),
                ('FS_To_Snowflake', 'FS/NFS', 'Snowflake', CURRENT_TIMESTAMP);
                """,

                """
                INSERT INTO job_template (sch_job_template_id, delete_after_completion, source_runtime_parameters, destination_runtime_parameters, source_connection_info, destination_connection_info, create_timestamp)
                VALUES
                ('73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa', false,
                '{"KAFKA_TOPIC":"weather_refined", "KAFKA_CONSUMER_ADLS":"kafka_to_adls_consumer"}',
                '{}',
                '{"STREAMSETS_KAFKA":"24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                '{"STREAMSETS_ADLS_GEN2" : "0a1c97e9-9695-4931-ba8b-05fe3de39b47:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                CURRENT_TIMESTAMP),
                ('838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa', false,
                '{"KAFKA_TOPIC": "[\n\"weather_refined\"\n]"}',
                '{"DeltaLake_Table": "hive_metastore.sanju.weather_events", "DeltaLake_Table_Location": "refined"}',
                '{"STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                '{"STREAMSETS_DATABRICKS_DELTA_LAKE" : "a57fb112-8bf6-42da-ad1d-c1db19b245d5:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                CURRENT_TIMESTAMP),
                ('fac8dee1-cff7-46a8-991c-746fc7705fc6:cd4694f6-2c60-11ec-988d-5b2e605d28aa', false,
                '{"REFINED_KAFKA_TOPIC": "weather_refined", "KAFKA_CONSUMER_GROUP": "cg_weather_snowflake_123451"}',
                '{"SNOWFLAKE_WAREHOUSE": "STREAMSETSSES_WH", "SNOWFLAKE_DB": "STREAMSETSSES_DB", "SNOWFLAKE_SCHEMA": "SANJU", "SNOWFLAKE_TABLE": "weather_events"}',
                '{"STREAMSETS_KAFKA" : "24f839bf-8548-4131-9752-f8f1e9b626ec:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                '{"STREAMSETS_SNOWFLAKE" : "0d43814f-98cd-4e65-875e-c84b0154d30f:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                CURRENT_TIMESTAMP),
                ('1acddc7e-06c2-4871-baae-3f55cec47be4:cd4694f6-2c60-11ec-988d-5b2e605d28aa', false,
                '{"BatchSize": "5000", "Dir": "/flight_data", "Filename_Pattern": "sample_10k.csv.bz2"}',
                '{"SNOWFLAKE_TABLE_NAME": "FLIGHTS"}',
                '{}',
                '{"STREAMSETS_SNOWFLAKE" : "0d43814f-98cd-4e65-875e-c84b0154d30f:cd4694f6-2c60-11ec-988d-5b2e605d28aa"}',
                CURRENT_TIMESTAMP);
                """,

                """
                INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
                SELECT p.ingestion_pattern_id, t.job_template_id
                FROM ingestion_pattern p, job_template t
                WHERE p.source = 'KAFKA' AND p.destination = 'ADLS'
                AND t.sch_job_template_id = '73bf3338-e52c-492b-ac68-7e0e572a6ae2:cd4694f6-2c60-11ec-988d-5b2e605d28aa';
                """,
                """
                INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
                SELECT p.ingestion_pattern_id, t.job_template_id
                FROM ingestion_pattern p, job_template t
                WHERE p.source = 'KAFKA' AND p.destination = 'DeltaLake'
                AND t.sch_job_template_id = '838b7cbc-68c4-44ba-bf2c-d856d95f5467:cd4694f6-2c60-11ec-988d-5b2e605d28aa';
                """,
                """
                INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
                SELECT p.ingestion_pattern_id, t.job_template_id
                FROM ingestion_pattern p, job_template t
                WHERE p.source = 'KAFKA' AND p.destination = 'Snowflake'
                AND t.sch_job_template_id = 'fac8dee1-cff7-46a8-991c-746fc7705fc6:cd4694f6-2c60-11ec-988d-5b2e605d28aa';
                """,
                """
                INSERT INTO ingestion_pattern_job_template_relationship (ingestion_pattern_id, job_template_id)
                SELECT p.ingestion_pattern_id, t.job_template_id
                FROM ingestion_pattern p, job_template t
                WHERE p.source = 'FS/NFS' AND p.destination = 'Snowflake'
                AND t.sch_job_template_id = '1acddc7e-06c2-4871-baae-3f55cec47be4:cd4694f6-2c60-11ec-988d-5b2e605d28aa';
                """
            ]
            try:
                for statement in template_sql:
                    self.db.session.execute(text(statement))
                self.db.session.commit()
                self.logger.log_msg('info', f"DB initialized with example job templates")

            except Exception as e:
                self.db.session.rollback()
                self.logger.log_msg('error', f"Failed to initialize the DB with example job templates: {e}")

    def check_tables_empty(self, tables):
        for table in tables:
            count = self.row_count(table)
            if count > 0:
                return False
        return True

    def write_to_table(self, record):
        with self.app.app_context():
            self.db.session.add(record)
            self.db.session.commit()

    def query_table(self, table, **kwargs):
        with self.app.app_context():
            result = self.db.session.query(table)
            # Apply filters for each key-value pair in kwargs
            for key, value in kwargs.items():
                column = getattr(table, key)
                result = result.filter(column == value)
            return result

    def row_count(self, table):
        with self.app.app_context():
            return self.db.session.query(table).count()


# Base class for models
class Base(DeclarativeBase):
    pass


# Define table schema classes

class User(UserMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


class IngestionPattern(Base):
    __tablename__ = 'ingestion_pattern'

    ingestion_pattern_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    create_timestamp: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)


class JobTemplate(Base):
    __tablename__ = 'job_template'

    job_template_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sch_job_template_id: Mapped[str] = mapped_column(String, nullable=False)
    delete_after_completion: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source_runtime_parameters: Mapped[dict] = mapped_column(JSON)
    destination_runtime_parameters: Mapped[dict] = mapped_column(JSON)
    source_connection_info: Mapped[dict] = mapped_column(JSON)
    destination_connection_info: Mapped[dict] = mapped_column(JSON)
    create_timestamp: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)


class IngestionPatternJobTemplateRelationship(Base):
    __tablename__ = 'ingestion_pattern_job_template_relationship'

    rel_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_pattern_id: Mapped[int] = mapped_column(Integer, ForeignKey('ingestion_pattern.ingestion_pattern_id'),
                                                      nullable=False)
    job_template_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_template.job_template_id'), nullable=False)


class JobInstance(Base):
    __tablename__ = 'job_instance'

    job_instance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String, nullable=False)
    job_run_count: Mapped[int] = mapped_column(String, nullable=False)
    job_template_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_template.job_template_id'), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    engine_id: Mapped[str] = mapped_column(String, nullable=False)
    pipeline_id: Mapped[str] = mapped_column(String, nullable=False)
    successful_run: Mapped[bool] = mapped_column(Boolean, nullable=False)
    input_record_count: Mapped[int] = mapped_column(Integer)
    output_record_count: Mapped[int] = mapped_column(Integer)
    error_record_count: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str] = mapped_column(String)
    start_time: Mapped[str] = mapped_column(TIMESTAMP)
    finish_time: Mapped[str] = mapped_column(TIMESTAMP)

# db_manager = DatabaseManager()
# db_manager.create_tables()
