import docker
import re
import configparser
import redis
import os

class FSCController(object):
    """
    A controller to manage FSC model execution.
    """

    def __init__(self, model_config):
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.fsc = 'fsc/latest'
        self.bucket = "world-modelers"
        self.key = "results/fsc_model/outputs"
        self.entrypoint=f"Rscript /main/main.R \
                          {model_config['year']} \
                          {model_config['country']} \
                          {model_config['production_decrease']} \
                          {model_config['fractional_reserve_access']} \
                           FSC_output"
        self.volumes = {f'{os.getcwd()}/outputs': {'bind': '/outputs', 'mode': 'rw'}}


    def run_model(self):
        """
        Run FSC model inside Docker container
        """
        self.model = self.containers.run(self.fsc, 
                                         volumes=self.volumes, 
                                         entrypoint=self.entrypoint,
                                         name='fsc',
                                         detach=True)
        return self.model


    def model_logs(self):
        """
        Return model logs
        """
        model_logs = self.model.logs()
        model_logs_decoded = model_logs.decode('utf-8')
        return model_logs_decoded