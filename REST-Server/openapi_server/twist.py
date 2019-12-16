import sys
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

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
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta

def run_twist(config):
    """
    Simple function to generate an DSSATController instance and run the model
    """
    twist = TWISTController(config)
    return twist.run_model()


class TWISTController(object):
    """
    A controller to manage TWIST model execution.
    """

    def __init__(self, model_config):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.name = 'multi_twist'
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.result_name = self.model_config['run_id'] 
        self.run_id = self.model_config['run_id']           
        self.bucket = "world-modelers"
        self.key = f"results/multi_twist_model/{self.result_name}"
        self.region = self.model_config.get('region','ALL')
        self.shock = self.model_config.get('shock','extreme')
        self.shock_year = self.model_config.get('shock_year','2018')
        self.crop = self.model_config.get('crop','wheat')
        self.entrypoint=f"python run_twist_with_prduction_shock.py --region {self.region} --shock {self.shock}"
        self.volumes = { f"{self.config['TWIST']['OUTPUT_PATH']}/output_data": {'bind': '/output_data', 'mode': 'rw'},}
        self.output = f"{self.config['TWIST']['OUTPUT_PATH']}/output_data/WM_price/WM_price_1976_2020_shock_year_{self.shock_year}_{self.region}_{self.shock}.csv"
        self.success_msg = 'Model run completed'

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=self.config['REDIS']['HOST'],
                        port=self.config['REDIS']['PORT'],
                        db=self.config['REDIS']['DB'])

        self.descriptions = {
                             'features': {
                                'WM_price_mean': '',
                                'WM_price_lower': '',
                                'WM_price_upper': '',
                                'WM_price_baseline_mean': '',
                                'WM_price_baseline_lower': '',
                                'WM_price_baseline_upper': '',
                                },
                             'parameters': {
                                'shock':'integer',
                                'shock_year': 'integer',
                                'crop': 'integer',
                                'region': 'string'
                                }
                            }

        logging.basicConfig(level=logging.INFO)


    def run_model(self):
        """
        Run Multi-TWIST model inside Docker container
        """
        time.sleep(1)
        logging.info(f"Running Multi-TWIST model run with ID: {self.run_id}")
        try:
            self.model = self.containers.run(self.name, 
                                             volumes=self.volumes, 
                                             entrypoint=self.entrypoint,
                                             detach=False,
                                             name=self.name)
            run_logs = self.model.decode('utf-8')

            if self.success_msg in run_logs:
                logging.info("Model run: SUCCESS")
                try:
                    self.storeResults()
                    logging.info("Model output: STORED")
                    try:
                        self.ingest2db()
                        # Success case requires storage to S3 AND ingest to DB
                        # if Success, update Redis accordingly
                        self.r.hmset(self.run_id, 
                            {'status': 'SUCCESS',
                             'bucket': self.bucket,
                             'key': self.key}
                             )                        
                    except Exception as e:
                        msg = f'DB ingest failure: {e}.'
                        logging.error(msg)
                        self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})                        
                except Exception as e:
                    msg = f'Output storage failure: {e}.'
                    logging.error(msg)
                    self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})
            else:
                logging.error(f"Model run FAIL: {run_logs}")
                self.r.hmset(self.run_id, {'status': 'FAIL', 'output': run_logs})
        except Exception as e:
            logging.error(f"Model run FAIL: {e}")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})

        # Prune old containers
        prior_container = self.containers.get(self.name)
        prior_container.remove()


    def storeResults(self):
        exists = os.path.exists(self.output)
        logging.info(self.output)
        logging.info(exists)
        if exists:
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(self.output, 
                           self.bucket, 
                           self.key, 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return "Output does not exist"


    def ingest2db(self):
        init_db()

        # Add metadata object to DB
        # TODO: add run_label and run_description
        logging.info("Storing metadata...")
        meta = Metadata(run_id=self.run_id, 
                        model=self.name,
                        run_description=f"{self.name} run with {self.shock} shock for {self.region} region(s)",
                        raw_output_link= f'https://s3.amazonaws.com/world-modelers/{self.key}'
                        ) 
        logging.info("Storing metadata...")
        db_session.add(meta)
        db_session.commit()

        # Add parameters to DB
        logging.info("Storing parameters...")
        for param_name, param_val in self.model_config.items():
            if param_name == 'run_id':
                pass
            else:
                param = Parameters(run_id=self.run_id,
                                  model=self.name,
                                  parameter_name=param_name,
                                  parameter_value=param_val,
                                  parameter_type=self.descriptions['parameters'][param_name])
                db_session.add(param)
                db_session.commit()

        # Process CSV and normalize it
        logging.info("Processing timeseries...")
        df = pd.read_csv(self.output)
        df = df.transpose().reset_index()
        df = df.rename(columns=dict(zip(list(df.columns),list(df.iloc[0]))))[1:]
        df = df.rename(columns={'Unnamed: 0':'Date'})
        df['datetime'] = df.Date.apply(lambda x: datetime(year=int(x.split('.')[1]),
                                                          month=int(x.split('.')[0]),
                                                          day=1)
                                      )
        del(df['Date'])
        df['run_id'] = self.run_id
        df['model'] = self.name

        base_cols = ['run_id','model','datetime']
        feature_cols = ['feature_name','feature_description','feature_value']

        for feature_name, feature_description in self.descriptions['features'].items():
            cols_to_select = base_cols + [feature_name]
            df_ = df[cols_to_select] # generate new interim DF
            df_['feature_name'] = feature_name
            df_['feature_description'] = feature_description
            df_['feature_value'] = df_[feature_name]
            df_ = df_[base_cols + feature_cols]

            # perform bulk insert of entire geopandas DF
            logging.info(f"Storing point data output for {feature_name}...")
            db_session.bulk_insert_mappings(Output, df_.to_dict(orient="records"))
            db_session.commit()            