import docker
import re
import configparser
import redis
import os
import shutil
import time
import logging
import boto3

class TWISTController(object):
    """
    A controller to manage TWIST model execution.
    """

    def __init__(self, model_config, output_path):
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.twist = 'wm-twist'
        self.result_path = output_path
        self.result_name = self.model_config['run_id']
        self.bucket = "world-modelers"
        self.key = f"results/twist_model/{self.result_name}.pkl"
        self.volumes = {self.result_path: {'bind': '/twist', 'mode': 'rw'}}

        logging.basicConfig(level=logging.INFO)


    def update_config(self):
        """
        Update TWIST_settings.py with appropriate configuration.

        Currently just allow start_year to be updated.

        TODO: verify other parameters to update.
        """
        if "start_year" in self.model_config:
            start_year = self.model_config["start_year"]
        else:
            start_year = 1975

        with open(f"{self.result_path}/main/TWIST_settings.py", 'r') as file:
            data = file.readlines()

        # now change the 2nd line, note that you have to add a newline
        data[78] = f"start_year = {start_year}\n"

        # and write everything back
        with open(f"{self.result_path}/main/TWIST_settings.py", 'w') as file:
            file.writelines( data )


    def run_model(self):
        """
        Run TWIST model inside Docker container
        """
        self.update_config()

        self.model = self.containers.run(self.twist, 
                                         volumes=self.volumes, 
                                         detach=True)
        return self.model


    def model_logs(self):
        """
        Return model logs
        """
        model_logs = self.model.logs()
        model_logs_decoded = model_logs.decode('utf-8')
        return model_logs_decoded
    
    
    def storeResults(self):
        result = f"{self.result_path}/TWIST_results.pkl"
        exists = os.path.exists(result)
        logging.info(exists)
        if exists:      
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(f"{result}", 
                           self.bucket, 
                           f"{self.key}", 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return result