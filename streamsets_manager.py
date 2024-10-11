import configparser
from streamsets.sdk import ControlHub


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