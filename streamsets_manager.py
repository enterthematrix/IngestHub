import configparser
import logging
from datetime import datetime
from time import time, sleep
from threading import Thread


from streamsets.sdk import ControlHub
from db_manager import JobInstance, DatabaseManager, JobTemplate

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# How often to check for updated Job Status
job_status_check_interval_secs = 10

# Max wait time for job completion
max_wait_time_for_job_secs = 4 * 60 * 60  # 4 hours

class StreamSetsManager:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = lambda option: option
        self._load_credentials()
        self.sch = ControlHub(credential_id=self.cred_id, token=self.cred_token)


    def _load_credentials(self):
        self.config.read('private/credentials.properties')
        self.cred_id = self.config.get("SECURITY", "CRED_ID")
        self.cred_token = self.config.get("SECURITY", "CRED_TOKEN")


    def get_job_template_static_params(self,job_template_id):
        job_template = self.sch.jobs.get(job_id=job_template_id)
        return job_template.static_parameters

    def get_job_template(self,job_template_id):
        return self.sch.jobs.get(job_id=job_template_id)

    # Starts a Job Template and returns a list of Job Template Instances
    def start_job_template(self, sch_job_template_id, runtime_parameters, instance_name_suffix,
                         suffix_parameter_name):
        try:
            # Find the Job Template
            job_template = self.get_job_template(sch_job_template_id)
            logger.info('Using Job template \'{}\''.format(job_template.job_name))
        except Exception as e:
            logger.error('Error: Job Template with ID \'' + sch_job_template_id + '\' not found.' + str(e))
            raise

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

    # Get metrics for all Job Template Instances once they complete
    def get_metrics(self,user, job_template_instances,job_template):
        # for job in job_template_instances:
        #     return f"Job:{job.job_name} started successfully by {current_user.name}"
        for job in job_template_instances:
            # Track each Job Template Instance in a separate thread to avoid blocking
            thread = Thread(target=self.wait_for_job_completion_and_get_metrics, args=(user, job_template, job))
            thread.start()

    # Waits for Job to complete before getting its metrics
    def wait_for_job_completion_and_get_metrics(self, user, job_template, job):
        start_seconds = time()
        elapsed_seconds = 0
        while elapsed_seconds < max_wait_time_for_job_secs:
            elapsed_seconds = time() - start_seconds
            job.refresh()
            if job.status.status == 'INACTIVE' or job.status.status == 'INACTIVE_ERROR':
                break
            sleep(job_status_check_interval_secs)
            logger.info(f"Waiting for job:{job.job_name} to finish")

        logger.info(f"Job:{job.job_name} finish running. Collecting metrics...")
        self.write_metrics_for_job(user, job_template, job)

    def write_metrics_for_job(self, user, job_template, job):
        job_metric = JobInstance()
        job.refresh()
        metrics = job.metrics[0]
        history = job.history[0]

        db = DatabaseManager()
        # get 'job_template.job_template_id' to be used as FK in 'job_instance' table
        job_template = db.query_table(table=JobTemplate, key='sch_job_template_id',
                                      value=job_template.job_id)

        # If job status color is RED, mark successful_run as False
        if job.status.status == 'INACTIVE' and history.color == 'GRAY':
            job_metric.successful_run = True
        else:
            job_metric.successful_run = False

        if history.error_message is None:
            job_metric.error_message = ''
        else:
            job_metric.error_message = history.error_message

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
        logger.info(f"Writing job metrics to the database...")
        db.write_to_table(job_metric)
        logger.info(f"Done writing job metrics to the database")


