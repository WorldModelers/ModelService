import docker
import re
import configparser
import redis
import os
import shutil
import time
import logging
import boto3
from rq import Queue

config = configparser.ConfigParser()
config.read('config.ini')
r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB']) 

q = Queue('high', connection=r)

def run_fsc(config, output_path):
    fsc = FSCController(config, output_path)
    return fsc.run_model()

def queue_fsc(config, output_path):
    return q.enqueue(run_fsc, config, output_path)

class FSCController(object):
    """
    A controller to manage FSC model execution.
    """

    def __init__(self, model_config, output_path):
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.fsc = 'fsc/latest'
        self.result_path = output_path
        self.result_name = self.model_config['run_id']
        self.run_id = self.model_config['run_id']
        self.bucket = "world-modelers"
        self.key = f"results/fsc_model/{self.result_name}.zip"
        self.success_msg = 'Writing output of'
        self.entrypoint=f"Rscript /main/main.R \
                          {model_config['year']} \
                          {model_config['country']} \
                          {model_config['production_decrease']} \
                          {model_config['fractional_reserve_access']} \
                           {self.result_name}"
        self.volumes = {self.result_path: {'bind': '/outputs', 'mode': 'rw'}}

        config = configparser.ConfigParser()
        config.read('config.ini')
        self.r = redis.Redis(host=config['REDIS']['HOST'],
                        port=config['REDIS']['PORT'],
                        db=config['REDIS']['DB'])      

        logging.basicConfig(level=logging.INFO)
        
        # try: # try to remove any prior container named `fsc`
        #     logging.info("Pruning old FSC containers...")
        #     prior_container = self.containers.get('fsc')
        #     removed = prior_container.remove()
        #     logging.info("Removed prior FSC container.")
        # except: # otherwise do nothing
        #     logging.info("No prior container to remove.")

    def run_model(self):
        """
        Run FSC model inside Docker container
        """

        # sleep to ensure that the originating API completes
        time.sleep(2)
        logging.info(f"Running model run with ID: {self.run_id}")

        # run model (note that logs are returned since detach=False)
        self.model = self.containers.run(self.fsc, 
                                         volumes=self.volumes, 
                                         entrypoint=self.entrypoint,
                                         detach=False)

        run_logs = self.model.decode('utf-8')

        if self.success_msg in run_logs:
            logging.info("Model run: SUCCESS")
            self.r.hmset(self.run_id, {'status': 'SUCCESS'})
            self.storeResults()
            logging.info("Model output: STORED")
        else:
            logging.info("Model run: FAIL")
            self.r.hmset(self.run_id, {'status': 'FAIL'})


    def model_logs(self):
        """
        Return model logs
        """
        model_logs = self.model.logs()
        model_logs_decoded = model_logs.decode('utf-8')
        return model_logs_decoded
    

    def storeResults(self):
        result = f"{self.result_path}/{self.result_name}"
        exists = os.path.isdir(result)
        logging.info(exists)
        if exists:
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