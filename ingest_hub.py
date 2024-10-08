import ast
import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired

from db_manager import User, IngestionPattern, IngestionPatternJobTemplateRelationship, JobTemplate
from forms import RegisterForm, LoginForm, TemplateForm


class IngestAppConfig:
    def __init__(self):
        self.app = Flask(__name__)
        self.configure_app()
        self.init_extensions()

    def configure_app(self):
        # Configure secret key and database URI
        self.app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamsets.db'  # Ensure this is set before initializing db

    def init_extensions(self):
        Bootstrap5(self.app)
        CKEditor(self.app)
        Gravatar(self.app,
                 size=100,
                 rating='g',
                 default='retro',
                 force_default=False,
                 force_lower=False,
                 use_ssl=False,
                 base_url=None)
        # Initialize SQLAlchemy after configuring the app
        # Initialize SQLAlchemy with the app
        self.db = SQLAlchemy(self.app)

    def create_tables(self):
        with self.app.app_context():
            self.db.create_all()

    def run(self):
        self.app.run(debug=True, port=5003)


# Authenticator class to handle user authentication
class Authenticator:
    def __init__(self, app, db):
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)
        self.db = db
        self.configure_user_loader()

    def configure_user_loader(self):
        @self.login_manager.user_loader
        def load_user(user_id):
            return self.db.get_or_404(User, user_id)


# Routes class to handle all routing and app logic
class IngestAppRoutes:
    def __init__(self, app, db, form_generator, job_template_manager):
        self.app = app
        self.db = db
        self.form_generator = form_generator
        self.job_template_manager = job_template_manager
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/")
        def about():
            if current_user.is_authenticated:
                return render_template("index.html", logged_in=current_user.is_authenticated)
            else:
                flash("Please login.")
                return redirect(url_for('login'))

        @self.app.route('/register', methods=["POST", "GET"])
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
                result = self.db.session.execute(self.db.select(User).where(User.email == new_user.email))
                user = result.scalar()
                if user:
                    flash("A user already exists with this email")
                    return redirect(url_for('register'))
                else:
                    self.db.session.add(new_user)
                    self.db.session.commit()
                    login_user(new_user)
                    return redirect(url_for("login"))

            return render_template("register.html", form=register_form)

        @self.app.route('/login', methods=["POST", "GET"])
        def login():
            login_form = LoginForm()
            if login_form.validate_on_submit():
                username = login_form.username.data
                password = login_form.password.data
                # Find user by email entered.
                result = self.db.session.execute(self.db.select(User).where(User.email == username))
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

            return render_template("login.html", form=login_form)

        @self.app.route('/templates', methods=['GET', 'POST'])
        @login_required
        def load_templates():
            form = TemplateForm()
            result = self.db.session.execute(self.db.select(IngestionPattern))
            patterns = result.scalars().all()
            sources, destinations = [], []
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

        @self.app.route('/source', methods=['GET', 'POST'])
        @login_required
        def source_runtime_parameters():
            source = request.args.get('source')
            destination = request.args.get('destination')
            job_template = self.job_template_manager.get_job_template(source, destination)
            source_configs = job_template.source_runtime_parameters
            DynamicForm = self.form_generator.generate_form(source_configs)
            form = DynamicForm()
            if form.validate_on_submit():
                updated_source_configs = {key: getattr(form, key).data for key in source_configs}
                return redirect(url_for('target_runtime_parameters', source=source, destination=destination,
                                        updated_source_configs=updated_source_configs,
                                        logged_in=current_user.is_authenticated))
            return render_template('source.html', form=form, logged_in=current_user.is_authenticated)

        @self.app.route('/target', methods=['GET', 'POST'])
        @login_required
        def target_runtime_parameters():
            source = request.args.get('source')
            destination = request.args.get('destination')
            source_configs = request.args.get('updated_source_configs')
            job_template = self.job_template_manager.get_job_template(source, destination)
            target_configs = job_template.destination_runtime_parameters
            DynamicForm = self.form_generator.generate_form(target_configs)
            form = DynamicForm()
            if form.validate_on_submit():
                updated_target_configs = {key: getattr(form, key).data for key in target_configs}
                return redirect(url_for('submit_job', source_configs=source_configs, target_configs=updated_target_configs,
                                        logged_in=current_user.is_authenticated))
            return render_template('target.html', form=form, logged_in=current_user.is_authenticated)

        @self.app.route('/submit-job', methods=['GET', 'POST'])
        @login_required
        def submit_job():
            source_configs = ast.literal_eval(request.args.get('source_configs'))
            target_configs = ast.literal_eval(request.args.get('target_configs'))
            return f"source:{source_configs} | target:{target_configs}"

        @self.app.route('/logout')
        def logout():
            logout_user()
            return redirect(url_for('login'))


# Job template manager to access job template information
class JobTemplateManager:
    def __init__(self, db):
        self.db = db

    def get_job_template(self, source, destination):
        patterns = self.db.session.query(IngestionPattern).filter(
            IngestionPattern.source == source,
            IngestionPattern.destination == destination
        ).all()
        for pattern in patterns:
            ingestion_pattern_id = pattern.ingestion_pattern_id

            templates = self.db.session.query(IngestionPatternJobTemplateRelationship).filter(
                IngestionPatternJobTemplateRelationship.ingestion_pattern_id == ingestion_pattern_id).all()
            for template in templates:
                job_template_id = template.job_template_id

                job_templates = self.db.session.query(JobTemplate).filter(
                    JobTemplate.job_template_id == job_template_id).all()

                for job_template in job_templates:
                    return job_template


# Form generator class dynamic form generation
class FormGenerator:
    @staticmethod
    def generate_form(fields_dict):
        class DynamicForm(FlaskForm):
            pass

        # Dynamically add StringFields using dictionary keys as labels and values as default values
        for label, default_value in fields_dict.items():
            setattr(DynamicForm, label, StringField(label, default=default_value, validators=[DataRequired()]))
        setattr(DynamicForm, 'next', SubmitField('Next'))
        return DynamicForm


if __name__ == "__main__":
    app_config = IngestAppConfig()
    # Make sure tables are created
    app_config.create_tables()
    # Configure authentication
    authenticator = Authenticator(app_config.app, app_config.db)
    # Instance for form generation
    form_generator = FormGenerator()
    # Instance for managing job templates
    job_template_manager = JobTemplateManager(app_config.db)
    # Set up app routes
    app_routes = IngestAppRoutes(app_config.app, app_config.db, form_generator, job_template_manager)
    # Start the app
    app_config.run()
