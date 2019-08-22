import docker
import re
import configparser
import redis
import os
import shutil
import time
import logging
import boto3

class DSSATController(object):
    """
    A controller to manage FSC model execution.
    """

    def __init__(self, model_config, output_path):
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.dssat = 'cvillalobosuf/dssat-pythia:develop'
        self.result_path = output_path
        self.result_name = self.model_config['run_id']             
        self.bucket = "world-modelers"
        self.key = f"results/dssat_model/{self.result_name}.zip"
        self.entrypoint=f"/app/pythia.sh --all /userdata/et_docker.json"
        self.volumes = {self.result_path: {'bind': '/userdata', 'mode': 'rw'}}
        self.volumes_from = "ethdata"
        self.mgmts = ["maize_irrig","maize_rf_0N","maize_rf_highN","maize_rf_lowN"]

        logging.basicConfig(level=logging.INFO)

    def run_model(self):
        """
        Run DSSAT model inside Docker container
        """
        self.model = self.containers.run(self.dssat, 
                                         volumes=self.volumes, 
                                         volumes_from=self.volumes_from,
                                         entrypoint=self.entrypoint,
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
        out = f"{self.result_path}/out"
        result = f"{self.result_path}/{self.result_name}"
        exists = os.path.isdir(out)
        logging.info(exists)
        if exists:
            # Make results for run_id
            os.mkdir(f"{self.result_path}/{self.result_name}")

            # Copy pp_* files to results directory
            for m in self.mgmts:
                shutil.copy(f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv",
                            f"{result}/pp_{m}.csv")
            shutil.make_archive(result, 'zip', result)            
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(f"{result}.zip", 
                           self.bucket, 
                           f"{self.key}", 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return result