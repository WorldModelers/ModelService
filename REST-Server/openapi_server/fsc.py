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

def run_fsc(config, output_path):
    """
    Simple function to generate an FSCController instance and run the model
    """
    fsc = FSCController(config, output_path)
    return fsc.run_model()


class FSCController(object):
    """
    A controller to manage FSC model execution.
    """

    def __init__(self, model_config, output_path):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
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

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=self.config['REDIS']['HOST'],
                        port=self.config['REDIS']['PORT'],
                        db=self.config['REDIS']['DB'])  

        logging.basicConfig(level=logging.INFO)                            


    def run_model(self):
        """
        Run FSC model inside Docker container
        """

        # sleep to ensure that the originating API completes
        logging.info(f"Running model run with ID: {self.run_id}")

        # run model (note that logs are returned since detach=False)
        try:
            self.model = self.containers.run(self.fsc, 
                                             volumes=self.volumes, 
                                             entrypoint=self.entrypoint,
                                             detach=False,
                                             name='fsc')

            run_logs = self.model.decode('utf-8')

            if self.success_msg in run_logs:
                logging.info("Model run: SUCCESS")          
                try:
                    self.storeResults()
                    logging.info("Model output: STORED")
                    self.r.hmset(self.run_id, 
                        {'status': 'SUCCESS',
                         'bucket': self.bucket,
                         'key': self.key}
                         )                    
                except:
                    msg = 'Output storage failure.'
                    logging.error(msg)
                    self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})
            else:
                logging.info("Model run: FAIL")
                self.r.hmset(self.run_id, {'status': 'FAIL', 'output': run_logs})

        except Exception as e:
            logging.error(f"Model run FAIL: {e}")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})
        
        # Prune old containers
        prior_container = self.containers.get('fsc')
        prior_container.remove()

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