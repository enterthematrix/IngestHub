import os
from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, TIMESTAMP, Boolean, ForeignKey, JSON

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamsets.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Define table schema
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


class IngestionPattern(Base):
    __tablename__ = 'ingestion_pattern'
    # __table_args__ = {'schema': 'streamsets'}

    ingestion_pattern_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    create_timestamp: Mapped[str] = mapped_column(TIMESTAMP, nullable=False)


class JobTemplate(Base):
    __tablename__ = 'job_template'
    # __table_args__ = {'schema': 'streamsets'}

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
    # __table_args__ = {'schema': 'streamsets'}

    rel_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_pattern_id: Mapped[int] = mapped_column(Integer,
                                                      ForeignKey('ingestion_pattern.ingestion_pattern_id'),
                                                      nullable=False)
    job_template_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_template.job_template_id'),
                                                 nullable=False)
    # schedule: Mapped[str] = mapped_column(String)


class JobInstance(Base):
    __tablename__ = 'job_instance'
    # __table_args__ = {'schema': 'streamsets'}

    job_instance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_run_id: Mapped[str] = mapped_column(String, nullable=False)
    job_template_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_template.job_template_id'),
                                                 nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    user_run_id: Mapped[str] = mapped_column(String, nullable=False)
    engine_id: Mapped[str] = mapped_column(String, nullable=False)
    pipeline_id: Mapped[str] = mapped_column(String, nullable=False)
    successful_run: Mapped[bool] = mapped_column(Boolean, nullable=False)
    input_record_count: Mapped[int] = mapped_column(Integer)
    output_record_count: Mapped[int] = mapped_column(Integer)
    error_record_count: Mapped[int] = mapped_column(Integer)
    error_message: Mapped[str] = mapped_column(String)
    start_time: Mapped[str] = mapped_column(TIMESTAMP)
    finish_time: Mapped[str] = mapped_column(TIMESTAMP)


with app.app_context():
    db.create_all()