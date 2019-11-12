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
import psycopg2
import csv

def run_dssat(config, output_path):
    """
    Simple function to generate an DSSATController instance and run the model
    """
    dssat = DSSATController(config, output_path)
    return dssat.run_model()


class DSSATController(object):
    """
    A controller to manage FSC model execution.
    """

    def __init__(self, model_config, output_path):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.dssat = 'cvillalobosuf/dssat-pythia:latest'
        self.result_path = output_path
        self.result_name = self.model_config['run_id'] 
        self.run_id = self.model_config['run_id']            
        self.bucket = "world-modelers"
        self.key = f"results/dssat_model/{self.result_name}"
        self.entrypoint=f"/app/pythia.sh --clean-work-dir --all /userdata/et_docker.json"
        self.volumes = {self.result_path: {'bind': '/userdata', 'mode': 'rw'}}
        self.volumes_from = "ethdata"
        self.mgmts = ["maize_irrig","maize_rf_0N","maize_rf_highN","maize_rf_lowN"]
        self.success_msg = 'Running simple analytics'

        if self.model_config["management_practice"] == "separate": 
            self.key += ".zip"
        else:
            self.key += ".csv"

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=self.config['REDIS']['HOST'],
                        port=self.config['REDIS']['PORT'],
                        db=self.config['REDIS']['DB'])             

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
            if "sample" in config:
                config.pop("sample")
        
        # Only produce a combined output if the configuration specifies to do so
        if self.model_config["management_practice"] == "combined":
            config["analytics_setup"]["singleOutput"] = True
        else:
            config["analytics_setup"]["singleOutput"] = False

        start_year = 1984
        # Update start year and number of years (if set in the user config)
        if "start_year" in self.model_config:
            start_year = int(self.model_config["start_year"])
            config["default_setup"]["startYear"] = start_year

            # We only bother setting number of years *if* start_year was specified
            if "number_years" in self.model_config:
                number_years = int(self.model_config["number_years"])
                # ensure that the number of years to run does not exceed 2018
                # valid example:
                # start_year = 2017
                # number_years = 2
                # so the model will run for 2 years (2017 and 2018)
                if start_year + number_years - 1 > 2018:
                    # ensure that number_years includes 2018 in this case
                    number_years = 2018 - start_year + 1
            else:
                number_years = 2018 - start_year + 1
            config["default_setup"]["nyers"] = number_years

        # Otherwise default to a 1984 start year and run through 2018
        else:
            config["default_setup"]["startYear"] = start_year
            config["default_setup"]["nyers"] = 34

        config["default_setup"]["sdate"] = f"{start_year}-01-01"
        config["default_setup"]["pfrst"] = f"{start_year}-03-01"
        config["default_setup"]["plast"] = f"{start_year}-05-20"

        with open(f"{self.result_path}/et_docker.json", "w") as f:
            f.write(json.dumps(config))
            f.close()


    def run_model(self):
        """
        Run DSSAT model inside Docker container
        """
        self.update_config()
        time.sleep(3)
        logging.info(f"Running model run with ID: {self.run_id}")
        try:
            self.model = self.containers.run(self.dssat, 
                                             volumes=self.volumes, 
                                             volumes_from=self.volumes_from,
                                             entrypoint=self.entrypoint,
                                             detach=False)
            run_logs = self.model.decode('utf-8')

            if self.success_msg in run_logs:
                logging.info("Model run: SUCCESS")          
                try:
                    self.storeResults()
                    logging.info("Model output: STORED")
                except:
                    msg = 'Output storage failure.'
                    logging.error(msg)
                    self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})
                self.r.hmset(self.run_id, 
                    {'status': 'SUCCESS',
                     'bucket': self.bucket,
                     'key': self.key}
                     )
                    
            else:
                logging.info("Model run: FAIL")
                self.r.hmset(self.run_id, {'status': 'FAIL', 'output': run_logs})
                
        except Exception as e:
            logging.info("Model run: FAIL")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})


    def storeResults(self):
        out = f"{self.result_path}/out"
        result = f"{self.result_path}/{self.result_name}"
        exists = os.path.isdir(out)
        logging.info(exists)
        if exists:
            
            # If separate (all management practices in separate files)
            if self.model_config["management_practice"] == "separate":            
                # Make results for run_id
                os.mkdir(f"{self.result_path}/{self.result_name}")

                # Copy pp_* files to results directory
                for m in self.mgmts:
                    shutil.copy(f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv",
                                f"{result}/pp_{m}.csv")
                shutil.make_archive(result, 'zip', result)
                to_upload = f"{result}.zip"
            
            
            # If combined (one single output file)
            elif self.model_config["management_practice"] == "combined":
                # Copy pp.csv file to results directory
                shutil.copy(f"{self.result_path}/out/eth_docker/test/pp.csv",
                            f"{result}.csv")
                to_upload = f"{result}.csv"
               
                # Insert into DB
                conn = psycopg2.connect(host=self.config["OUTPUTDB"]["DB"],database="output", user=self.config["OUTPUTDB"]["USER"], password=self.config["OUTPUTDB"]["PASSWORD"])
                cur = conn.cursor()
                rid = self.result_name.lower()
                cur.execute(f"SELECT * FROM rundata where run_id = '{rid}';")
                results = cur.fetchall()
                if len(results) == 0: 
                    with open(f"{result}.csv", 'r') as f:
                        reader = csv.reader(f)
                        next(reader)
                        for row in reader:
                            lat = row[0]
                            lon = row[1]
                            hwam = row[24]
                            sdat = row[16]
                            statement = f"insert into rundata (run_id,x,y,feature,value,datetime) values ('{self.result_name}',{lat},{lon},'yield',{hwam},'{sdat}')"
                            cur.execute(statement)
                        conn.commit()
                conn.close()
                
            # Otherwise, provide just the management practice of interest
            else:
                m = self.model_config["management_practice"]
                shutil.copy(f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv",
                            f"{result}.csv")
                to_upload = f"{result}.csv"    
                
                # Insert into DB
                conn = psycopg2.connect(host=self.config["OUTPUTDB"]["DB"],database="output", user=self.config["OUTPUTDB"]["USER"], password=self.config["OUTPUTDB"]["PASSWORD"])
                cur = conn.cursor()
                rid = self.result_name.lower()
                cur.execute(f"SELECT * FROM rundata where run_id = '{rid}';")
                results = cur.fetchall()
                if len(results) == 0:
                    with open(f"{result}.csv", 'r') as f:
                        reader = csv.reader(f)
                        next(reader)
                        for row in reader:
                            lat = row[0]
                            lon = row[1]
                            hwam = row[24]
                            sdat = row[16]
                            statement = f"insert into rundata (run_id,x,y,feature,value,datetime) values ('{self.result_name}',{lat},{lon},'yield',{hwam},'{sdat}')"
                            cur.execute(statement)
                        conn.commit()
                conn.close()
                    
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(to_upload, 
                           self.bucket, 
                           self.key, 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return result
