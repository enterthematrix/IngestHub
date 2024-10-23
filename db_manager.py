import os
from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, TIMESTAMP, Boolean, ForeignKey, JSON


# Database and Flask Configuration as a separate class
class Config:
    SECRET_KEY = os.environ.get('FLASK_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///streamsets.db'


# Flask App Class
class DatabaseManager:
    def __init__(self):
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


db_manager = DatabaseManager()
db_manager.create_tables()
