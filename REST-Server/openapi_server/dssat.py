import docker
import re
import configparser
import redis
import os
import shutil
import time
import logging
import boto3
import json

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
        self.key = f"results/dssat_model/{self.result_name}.csv"
        self.entrypoint=f"/app/pythia.sh --all /userdata/et_docker.json"
        self.volumes = {self.result_path: {'bind': '/userdata', 'mode': 'rw'}}
        self.volumes_from = "ethdata"
        self.mgmts = ["maize_irrig","maize_rf_0N","maize_rf_highN","maize_rf_lowN"]

        logging.basicConfig(level=logging.INFO)


    def update_config(self):
        """
        Update et_docker.json file with user-submitted config
        """
        with open(f"{self.result_path}/et_docker.json", "r") as f:
            config = json.loads(f.read())
            f.close()

        # If a number of samples is provided, use that
        if self.model_config["samples"] > 0:
            config["sample"] = self.model_config["samples"]
        else:
            # Otherwise, remove the `sample` key and run the 
            # entire region (Ethiopia)
            config.pop("sample")

        with open(f"{self.result_path}/et_docker.json", "w") as f:
            f.write(json.dumps(config))
            f.close()


    def run_model(self):
        """
        Run DSSAT model inside Docker container
        """
        self.update_config()
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
            # Copy pp.csv file to results directory
            shutil.copy(f"{self.result_path}/out/eth_docker/test/pp.csv",
                        f"{result}.csv")
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(f"{result}.csv", 
                           self.bucket, 
                           f"{self.key}", 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return result