import configparser
from datetime import datetime
from time import time, sleep
from threading import Thread

from streamsets.sdk import ControlHub
from db_manager import JobInstance, JobTemplate
from ingest_hub import Logger

# job status check frequency
JOB_STATUS_CHECK_INTERVAL_SECS = 10
# max wait time for job completion
MAX_WAIT_TIME_FOR_JOB_SECS = 4 * 60 * 60  # 4 hours
# ControlHub Credentials file
CREDENTIALS_PROPERTIES = 'private/credentials.properties'


class StreamSetsManager:
    def __init__(self, db_manager):
        self.logger = Logger()
        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option
        try:
            self._load_credentials()
            self.db_manager = db_manager
            self.sch = ControlHub(credential_id=self.cred_id, token=self.cred_token)
        except Exception as e:
            self.logger.log_msg('error', f"Failed to initialize StreamSetsManager: {e}")
            raise

    def _load_credentials(self):
        try:
            self.config.read(CREDENTIALS_PROPERTIES)
            self.cred_id = self.config.get("SECURITY", "CRED_ID")
            self.cred_token = self.config.get("SECURITY", "CRED_TOKEN")
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            self.logger.log_msg('error', f"Error loading credentials: {e}")
            raise

    def get_job_template_static_params(self, job_template_id):
        try:
            job_template = self.sch.jobs.get(job_id=job_template_id)
            return job_template.static_parameters
        except Exception as e:
            self.logger.log_msg('error',
                                f"Error retrieving static parameters for job template ID '{job_template_id}': {e}")
            return None

    def get_job_template(self, job_template_id):
        try:
            return self.sch.jobs.get(job_id=job_template_id)
        except Exception as e:
            self.logger.log_msg('error', f"Error retrieving job template with ID '{job_template_id}': {e}")
            return None

    def start_job_template(self, sch_job_template_id, runtime_parameters, instance_name_suffix, suffix_parameter_name):
        try:
            job_template = self.get_job_template(sch_job_template_id)
            if job_template is None:
                raise ValueError("Job template not found")
            self.logger.log_msg('info', f"Using Job template '{job_template.job_name}'")

            suffix_map = {
                'Counter': 'COUNTER',
                'Timestamp': 'TIMESTAMP'
            }
            suffix = suffix_map.get(instance_name_suffix, 'PARAM_VALUE')
            return self.sch.start_job_template(
                job_template,
                runtime_parameters=runtime_parameters,
                instance_name_suffix=suffix,
                delete_after_completion=job_template.delete_after_completion,
                parameter_name=suffix_parameter_name if suffix == 'PARAM_VALUE' else None
            )
        except Exception as e:
            self.logger.log_msg('error', f"Error starting job template with ID '{sch_job_template_id}': {e}")
            return None

    def get_metrics(self, user, job_template_instances, job_template):
        for job in job_template_instances:
            thread = Thread(target=self.wait_for_job_completion_and_get_metrics, args=(user, job_template, job))
            thread.start()

    def wait_for_job_completion_and_get_metrics(self, user, job_template, job):
        with self.db_manager.app.app_context():
            start_seconds = time()
            elapsed_seconds = 0
            while elapsed_seconds < MAX_WAIT_TIME_FOR_JOB_SECS:
                try:
                    elapsed_seconds = time() - start_seconds
                    job.refresh()
                    if job.status.status in ['INACTIVE', 'INACTIVE_ERROR']:
                        break
                    sleep(JOB_STATUS_CHECK_INTERVAL_SECS)
                    self.logger.log_msg('info', f"Waiting for job: [{job.job_name}] to finish")
                except Exception as e:
                    self.logger.log_msg('error',
                                        f"Error while waiting for job completion for job '{job.job_name}': {e}")
                    break

            self.logger.log_msg('info', f"Job: [{job.job_name}] finished running. Collecting metrics...")
            self.write_metrics_for_job(user, job_template, job)

    def write_metrics_for_job(self, user, job_template, job):
        try:
            job_metric = JobInstance()
            job.refresh()
            metrics = job.metrics[0]
            history = job.history[0]

            job_template = self.db_manager.query_table(JobTemplate, sch_job_template_id=job_template.job_id).first()

            job_metric.successful_run = (job.status.status == 'INACTIVE' and history.color == 'GRAY')
            job_metric.error_message = history.error_message if history.error_message else ''

            job_metric.user_id = user
            job_metric.job_id = job.job_id
            job_metric.job_template_id = job_template.job_template_id
            job_metric.job_run_count = metrics.run_count
            job_metric.engine_id = metrics.sdc_id
            job_metric.pipeline_id = job.pipeline_id
            job_metric.input_record_count = metrics.input_count
            job_metric.output_record_count = metrics.output_count
            job_metric.error_record_count = metrics.total_error_count
            job_metric.start_time = datetime.fromtimestamp(history.start_time / 1000.0)
            job_metric.finish_time = datetime.fromtimestamp(history.finish_time / 1000.0)

            self.logger.log_msg('info', "Writing job metrics to the database...")
            self.db_manager.write_to_table(job_metric)
            self.logger.log_msg('info', "Done writing job metrics to the database")
        except Exception as e:
            self.logger.log_msg('error', f"Failed to write job metrics for job '{job.job_name}': {e}")