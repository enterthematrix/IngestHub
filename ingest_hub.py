import ast
import math
import os

import pyfiglet
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from db_manager import User, IngestionPattern, IngestionPatternJobTemplateRelationship, JobTemplate, DatabaseManager, \
    JobInstance
from forms import RegisterForm, LoginForm, TemplateForm, FormGenerator, JobInstanceSuffixForm
from ingesthub_logger import Logger

JOBS_PER_PAGE = 20


class IngestHubConfig:
    def __init__(self):
        self.logger = Logger(self.__class__.__name__)
        self.app = Flask(__name__)
        self.db_manager = db_manager
        self.configure_app()
        self.init_extensions()
        print(pyfiglet.Figlet(font='big', width=80).renderText('IngestHub'))

    def configure_app(self):
        # Configure secret key and database URI
        self.app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
        self.app.config[
            'SQLALCHEMY_DATABASE_URI'] = 'sqlite:///streamsets.db'  # Ensure this is set before initializing db

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
        # Initialize DB after configuring the app
        db_manager.db.init_app(self.app)

    def initialize_db(self):
        try:
            self.db_manager.create_tables()
            if self.db_manager.check_tables_empty([User, IngestionPattern, JobTemplate,
                                                   IngestionPatternJobTemplateRelationship, JobInstance]):
                self.logger.log_msg("info", f"Initializing the database with example job templates...")
                self.db_manager.load_templates()
            else:
                self.logger.log_msg("info", "Example template data already loaded, skipping loading of templates data")
        except Exception as e:
            self.logger.log_msg("error", f"Error in database initialization: {e}")
            self.db_manager.db.session.rollback()

    def run(self):
        self.app.run(debug=True, port=5003)


# Authenticator class to handle user authentication
class IngestHubAuthenticator:
    def __init__(self, app):
        self.logger = Logger(self.__class__.__name__).get_logger()
        self.login_manager = LoginManager()
        try:
            self.login_manager.init_app(app)
            self.db_manager = db_manager
            self.configure_user_loader()
        except Exception as e:
            self.logger.error(f"Error initializing IngestHubAuthenticator: {e}")

    def configure_user_loader(self):
        @self.login_manager.user_loader
        def load_user(user_id):
            try:
                return self.db_manager.db.get_or_404(User, user_id)
            except Exception as e:
                self.logger.error(f"Error loading user with ID {user_id}: {e}")
                return None  # Optionally return None or handle as needed


# Routes class to handle all routing and app logic
class IngestHubRoutes:
    def __init__(self, app, db_manager, form_generator, job_template_manager):
        self.logger = Logger(self.__class__.__name__)
        self.app = app
        self.db_manager = db_manager
        self.form_generator = form_generator
        self.job_template_manager = job_template_manager
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/")
        def about():
            try:
                if current_user.is_authenticated:
                    return render_template("index.html", logged_in=current_user.is_authenticated)
                else:
                    flash("Please login.", "info")
                    return redirect(url_for('login'))
            except Exception as e:
                self.logger.log_msg("error", f"Error in about route: {e}")
                flash("An error occurred.", "error")
                return redirect(url_for('login'))

        @self.app.route('/register', methods=["POST", "GET"])
        def register():
            register_form = RegisterForm()
            if register_form.validate_on_submit():
                try:
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
                    result = self.db_manager.db.session.execute(
                        self.db_manager.db.select(User).where(User.email == new_user.email)
                    )
                    user = result.scalar()
                    if user:
                        flash("A user already exists with this email", "warning")
                        return redirect(url_for('register'))
                    else:
                        self.db_manager.db.session.add(new_user)
                        self.db_manager.db.session.commit()
                        login_user(new_user)
                        return redirect(url_for("login"))
                except Exception as e:
                    self.logger.log_msg("error", f"Error in register route: {e}")
                    flash("An error occurred during registration.", "error")
                    self.db_manager.db.session.rollback()
            return render_template("register.html", form=register_form)

        @self.app.route('/login', methods=["POST", "GET"])
        def login():
            login_form = LoginForm()
            if login_form.validate_on_submit():
                try:
                    username = login_form.username.data
                    password = login_form.password.data
                    result = self.db_manager.db.session.execute(
                        self.db_manager.db.select(User).where(User.email == username)
                    )
                    user = result.scalar()

                    if not user:
                        flash("This username does not exist, please try again.", "warning")
                        return redirect(url_for('login'))
                    elif not check_password_hash(user.password, password):
                        flash('Password incorrect, please try again.', "warning")
                        return redirect(url_for('login'))
                    else:
                        login_user(user)
                        return redirect(url_for("load_templates"))
                except Exception as e:
                    self.logger.log_msg("error", f"Error in login route: {e}")
                    flash(f"Error in login route: {e}", "error")
            return render_template("login.html", form=login_form)

        @self.app.route('/templates', methods=['GET', 'POST'])
        @login_required
        def load_templates():
            try:
                form = TemplateForm()
                result = self.db_manager.db.session.execute(self.db_manager.db.select(IngestionPattern))
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
                    return redirect(
                        url_for('source_runtime_parameters', source=selected_source, destination=selected_destination,
                                logged_in=current_user.is_authenticated))
                return render_template('templates.html', form=form, logged_in=current_user.is_authenticated)
            except Exception as e:
                self.logger.log_msg("error", f"Error in load_templates route: {e}")
                flash(f"Error in load_templates route: {e}", "error")
                return redirect(url_for('about'))

        @self.app.route('/source', methods=['GET', 'POST'])
        @login_required
        def source_runtime_parameters():
            try:
                source = request.args.get('source')
                destination = request.args.get('destination')
                job_template = self.job_template_manager.get_job_template(source, destination)
                source_configs = job_template.source_runtime_parameters
                dynamic_form = self.form_generator.generate_form(source_configs, job_template.sch_job_template_id,
                                                                 submit_text="Next")
                form = dynamic_form()
                if form.validate_on_submit():
                    updated_source_configs = {key: getattr(form, key).data for key in source_configs}
                    return redirect(url_for('target_runtime_parameters', source=source, destination=destination,
                                            updated_source_configs=updated_source_configs,
                                            logged_in=current_user.is_authenticated))
                return render_template('source.html', form=form, logged_in=current_user.is_authenticated)
            except Exception as e:
                self.logger.log_msg("error", f"Error in source_runtime_parameters route: {e}")
                flash(f"Error in source_runtime_parameters route: {e}", "error")
                return redirect(url_for('load_templates'))

        @self.app.route('/target', methods=['GET', 'POST'])
        @login_required
        def target_runtime_parameters():
            try:
                source = request.args.get('source')
                destination = request.args.get('destination')
                source_configs = request.args.get('updated_source_configs')
                job_template = self.job_template_manager.get_job_template(source, destination)
                target_configs = job_template.destination_runtime_parameters
                dynamic_form = self.form_generator.generate_form(target_configs, job_template.sch_job_template_id,
                                                                 submit_text="Next")
                form = dynamic_form()
                if form.validate_on_submit():
                    updated_target_configs = {key: getattr(form, key).data for key in target_configs}
                    return redirect(url_for('job_suffix', job_template_id=job_template.sch_job_template_id,
                                            source_configs=source_configs, target_configs=updated_target_configs,
                                            logged_in=current_user.is_authenticated))
                return render_template('target.html', form=form, logged_in=current_user.is_authenticated)
            except Exception as e:
                self.logger.log_msg("error", f"Error in target_runtime_parameters route: {e}")
                flash(f"Error in target_runtime_parameters route: {e}", "error")
                return redirect(url_for('load_templates'))

        @self.app.route('/job-suffix', methods=['GET', 'POST'])
        @login_required
        def job_suffix():
            try:
                source_configs = ast.literal_eval(request.args.get('source_configs'))
                target_configs = ast.literal_eval(request.args.get('target_configs'))
                suffix_parameters = source_configs | target_configs
                sch_job_template_id = request.args.get('job_template_id')
                form = JobInstanceSuffixForm()
                suffix_list = ['Counter', 'Timestamp', 'Parameter Value']
                form.instance_name_suffix.choices.extend([(suffix, suffix) for suffix in suffix_list])
                form.suffix_parameter_name.choices.extend(
                    [(suffix_parameter, suffix_parameter) for suffix_parameter in suffix_parameters])

                if form.validate_on_submit():
                    instance_name_suffix = form.instance_name_suffix.data
                    suffix_parameter_name = form.suffix_parameter_name.data
                    return redirect(
                        url_for('submit_job', job_template_id=sch_job_template_id, runtime_parameters=suffix_parameters,
                                suffix_parameter_name=suffix_parameter_name, instance_name_suffix=instance_name_suffix,
                                logged_in=current_user.is_authenticated))
                return render_template('job-suffix.html', form=form, logged_in=current_user.is_authenticated)
            except Exception as e:
                self.logger.log_msg("error", f"Error in job_suffix route: {e}")
                flash(f"Error in job_suffix route: {e}", "error")
                return redirect(url_for('load_templates'))

        @self.app.route('/submit-job', methods=['GET', 'POST'])
        @login_required
        def submit_job():
            try:
                runtime_parameters = ast.literal_eval(request.args.get('runtime_parameters'))
                sch_job_template_id = request.args.get('job_template_id')
                instance_name_suffix = request.args.get('instance_name_suffix')
                suffix_parameter_name = request.args.get('suffix_parameter_name')
                from streamsets_manager import StreamSetsManager
                streamsets_manager = StreamSetsManager(self.db_manager)
                jobs = streamsets_manager.start_job_template(sch_job_template_id, runtime_parameters,
                                                             instance_name_suffix,
                                                             suffix_parameter_name)
                job_template = streamsets_manager.get_job_template(sch_job_template_id)
                user = current_user.name
                with self.db_manager.app.app_context():
                    streamsets_manager.get_metrics(user=user, job_template_instances=jobs,
                                                   job_template=job_template)

                for job in jobs:
                    self.logger.log_msg('info', f"Job:[{job.job_name}] started successfully by [{current_user.name}]")
                    flash(f"Job: [{job.job_name}] submitted successfully", "success")
                    return redirect(url_for('recent_jobs', logged_in=current_user.is_authenticated))
            except Exception as e:
                self.logger.log_msg("error", f"Error in submit_job route: {e}")
                flash(f"Error in submit_job route: {e}", "error")
                return redirect(url_for('load_templates'))

        @self.app.route('/jobs', methods=['GET', 'POST'])
        @login_required
        def recent_jobs():
            try:
                jobs_per_page = JOBS_PER_PAGE
                page = request.args.get('page', 1, type=int)

                total_rows = self.db_manager.row_count(table=JobInstance)
                total_pages = math.ceil(total_rows / jobs_per_page)
                jobs = (
                    self.db_manager.db.session.query(JobInstance)
                    .order_by(desc(JobInstance.start_time))
                    .offset((page - 1) * jobs_per_page)
                    .limit(jobs_per_page)
                    .all()
                )

                # Create a pagination object
                pagination = {
                    'page': page,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages,
                    'prev_num': page - 1 if page > 1 else None,
                    'next_num': page + 1 if page < total_pages else None,
                }
                return render_template('jobs.html', jobs=jobs, pagination=pagination, total_pages=total_pages,
                                       logged_in=current_user.is_authenticated)
            except Exception as e:
                self.logger.log_msg("error", f"Error in recent_jobs route: {e}")
                flash(f"Error in recent_jobs route: {e}")
                return redirect(url_for('about'))

        @self.app.route('/logout')
        def logout():
            try:
                logout_user()
                return redirect(url_for('login'))
            except Exception as e:
                self.logger.log_msg("error", f"Error in logout route: {e}")
                flash(f"Error in logout route: {e}")
                return redirect(url_for('login'))


# Job template manager to access job template information
class JobTemplateManager:
    def __init__(self):
        self.logger = Logger(self.__class__.__name__).get_logger()
        self.db = db_manager.db

    def get_job_template(self, source, destination):
        try:
            patterns = self.db.session.query(IngestionPattern).filter(
                IngestionPattern.source == source,
                IngestionPattern.destination == destination
            ).all()

            for pattern in patterns:
                ingestion_pattern_id = pattern.ingestion_pattern_id

                templates = self.db.session.query(IngestionPatternJobTemplateRelationship).filter(
                    IngestionPatternJobTemplateRelationship.ingestion_pattern_id == ingestion_pattern_id
                ).all()

                for template in templates:
                    job_template_id = template.job_template_id

                    job_templates = self.db.session.query(JobTemplate).filter(
                        JobTemplate.job_template_id == job_template_id
                    ).all()

                    for job_template in job_templates:
                        return job_template  # Return the first job template found

            # If no job templates were found, log that information
            self.logger.warning(f"No job templates found for source '{source}' and destination '{destination}'.")
            return None  # Return None if no job template is found

        except Exception as e:
            self.logger.error(
                f"Error retrieving job template for source '{source}' and destination '{destination}': {e}")
            return None  # Optionally return None or handle as needed


if __name__ == "__main__":
    # initialize DB manager
    db_manager = DatabaseManager()
    ingest_hub = IngestHubConfig()
    app = ingest_hub.app
    # Make sure tables are created
    ingest_hub.initialize_db()
    # Configure authentication
    authenticator = IngestHubAuthenticator(ingest_hub.app)
    # Instance for form generation
    form_generator = FormGenerator()
    # Instance for managing job templates
    job_template_manager = JobTemplateManager()
    # Set up app routes
    app_routes = IngestHubRoutes(ingest_hub.app, ingest_hub.db_manager, form_generator,
                                 job_template_manager)
    # Start the app
    ingest_hub.run()
