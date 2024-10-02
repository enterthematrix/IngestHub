import ast
import os
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, TIMESTAMP, Boolean, ForeignKey, JSON
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired

# Import your forms from the forms.py
from forms import RegisterForm, LoginForm, TemplateForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamsets.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES
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

# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


# Create a user_loader callback to re-load user from the session
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
@login_required
def about():
    if current_user.is_authenticated:
        print(f"User logged in?: {current_user.is_authenticated}")
        return render_template("index.html", logged_in=current_user.is_authenticated)
    else:
        flash("You need to login or register to comment.")
        return redirect(url_for('login'))


@app.route('/register', methods=["POST", "GET"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        hash_and_salted_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=register_form.email.data,
            name=register_form.name.data,
            password=hash_and_salted_password
        )
        # Check if a user already exists with this email
        result = db.session.execute(db.select(User).where(User.email == new_user.email))
        user = result.scalar()
        if user:
            flash("A user already exists with this email")
            return redirect(url_for('register'))
        else:
            db.session.add(new_user)
            db.session.commit()
            # Log in and authenticate user after adding details to database.
            login_user(new_user)
            return redirect(url_for("login"))
            # return render_template("about.html")

    return render_template("register.html", form=register_form)


@app.route('/login', methods=["POST", "GET"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        # Find user by email entered.
        result = db.session.execute(db.select(User).where(User.email == username))
        user = result.scalar()

        if not user:
            flash("This username does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for("load_templates"))
            # return render_template("about.html",logged_in=current_user.is_authenticated)

    return render_template("login.html", form=login_form)


@app.route('/templates', methods=['GET', 'POST'])
@login_required
def load_templates():
    form = TemplateForm()
    result = db.session.execute(db.select(IngestionPattern))
    patterns = result.scalars().all()
    sources = []
    destinations = []
    for pattern in patterns:
        if pattern.source not in sources:
            sources.append(pattern.source)
        if pattern.destination not in destinations:
            destinations.append(pattern.destination)

    form.source.choices.extend([(source, source) for source in sources])
    form.destination.choices.extend([(destination, destination) for destination in destinations])

    if form.validate_on_submit():
        selected_source = form.source.data
        selected_destination = form.destination.data
        return redirect(url_for('source_runtime_parameters', source=selected_source, destination=selected_destination,
                                logged_in=current_user.is_authenticated))

    return render_template('templates.html', form=form, logged_in=current_user.is_authenticated)


def generate_form(fields_dict):
    # Create a dynamic form class
    class DynamicForm(FlaskForm):
        pass

    # Dynamically add StringFields using dictionary keys as labels and values as default values
    for label, default_value in fields_dict.items():
        setattr(DynamicForm, label, StringField(label, default=default_value, validators=[DataRequired()]))
    setattr(DynamicForm, 'next', SubmitField('Next'))
    return DynamicForm


def get_job_template(source, destination):
    global ingestion_pattern_id, sch_job_template_id, job_template_id, job_template
    patterns = db.session.query(IngestionPattern).filter(
        IngestionPattern.source == source,
        IngestionPattern.destination == destination
    ).all()
    for pattern in patterns:
        ingestion_pattern_id = pattern.ingestion_pattern_id

    templates = db.session.query(IngestionPatternJobTemplateRelationship).filter(
        IngestionPatternJobTemplateRelationship.ingestion_pattern_id == ingestion_pattern_id).all()
    for template in templates:
        job_template_id = template.job_template_id

    job_templates = db.session.query(JobTemplate).filter(
        JobTemplate.job_template_id == job_template_id).all()

    for job_template in job_templates:
        job_template = job_template
    return job_template


@app.route('/source', methods=['GET', 'POST'])
@login_required
def source_runtime_parameters():
    source = request.args.get('source')
    destination = request.args.get('destination')
    job_template = get_job_template(source, destination)
    source_configs = job_template.source_runtime_parameters
    target_configs = job_template.destination_runtime_parameters
    # Create the dynamic form using the dictionary
    DynamicForm = generate_form(source_configs)
    form = DynamicForm()
    if form.validate_on_submit():
        # Collect field data from dynamically generated form
        updated_source_configs = {key: getattr(form, key).data for key in source_configs}
        if target_configs:
            return redirect(url_for('target_runtime_parameters', source=source, destination=destination,
                                    updated_source_configs=updated_source_configs,
                                    logged_in=current_user.is_authenticated))
        else:
            return "No No No"

    return render_template('source.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/target', methods=['GET', 'POST'])
@login_required
def target_runtime_parameters():
    source = request.args.get('source')
    destination = request.args.get('destination')
    source_configs = ast.literal_eval(request.args.get('updated_source_configs')).items()
    # for key,value in ast.literal_eval(request.args.get('updated_source_configs')).items():
    #     print(f"{key}:{value}")
    job_template = get_job_template(source, destination)
    target_configs = job_template.destination_runtime_parameters
    # Create the dynamic form using the dictionary
    DynamicForm = generate_form(target_configs)
    form = DynamicForm()
    if form.validate_on_submit():
        # Collect field data from dynamically generated form
        updated_target_configs = {key: getattr(form, key).data for key in target_configs}
        return redirect(url_for('load_templates', source_configs=source_configs, target_configs=updated_target_configs,
                                logged_in=current_user.is_authenticated))

    return render_template('target.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, port=5003)
