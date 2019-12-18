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
import yaml
from shapely.geometry import Point
from datetime import datetime, timedelta

def get_param_type(t):
    """
    Determine SQL type based on parameter type
    Note: this may be model specific
    """
    if t == 'ChoiceParameter':
        return 'string' # for some models this may be an integer
    elif t == 'TimeParameter':
        return 'integer' # for some models this may be a string


def load_yaml(metadata_file):
    """
    Generate features and parameter dictionary lookups
    based on a model metadata file
    """
    with open(metadata_file, 'r') as stream:
        model = yaml.safe_load(stream)
    
    parameters = {}
    for p in model['parameters']:
        parameters[p['name']] = get_param_type(p['metadata']['type'])
        
    features = {}
    for o in model['outputs']:
        features[o['name']] = o['description'] 

    return {'features': features, 'parameters': parameters}


def gen_output_path(output_base_path, 
                    scenario_type, 
                    start_year, 
                    end_year, 
                    crop, 
                    shocked_region=None, shock_severity=None, scenario_start_year=None):
    """
    Generate output path based on the given run configuration
    """    
    if scenario_type == 'production_failure_scenario':
        file_name = f'world_market_price_{crop}_'\
                    f'{start_year}_{end_year}_shock_{scenario_start_year}_{shocked_region}_'\
                    f'{shock_severity}.csv'
        return f"{output_base_path}/production_shock/{file_name}"

    elif scenario_type == 'forecast':
        file_name = f'world_market_price_{crop}_forecast_{start_year}_{end_year}.csv'
        return f"{output_base_path}/forecast/{file_name}"

    elif scenario_type == 'counterfactual_reserve':
        file_name = f'world_market_price_counterfactual_reserve_{start_year}_{end_year}.csv'
        return f"{output_base_path}/{file_name}"

    elif scenario_type == 'historical':
        file_name = f'world_market_price_historical_{start_year}_{end_year}.csv'
        return f"{output_base_path}/{file_name}"  


def gen_entrypoint(scenario_type, 
                   start_year, 
                   end_year, 
                   crop, 
                   shocked_region=None, shock_severity=None, scenario_start_year=None):
    """
    Generate a Docker entrypoint based on the provided configuration
    """    
    base = 'python run_multi_twist.py'
    if scenario_type == 'production_failure_scenario':
        entrypoint = f'{base}  --scenario_type {scenario_type} --shocked_region {shocked_region} '\
                     f'--shock_severity {shock_severity} --crop {crop} --start_year {start_year} '\
                     f'--end_year {end_year}'

    else:
        entrypoint = f'{base}  --scenario_type {scenario_type} --crop {crop} --start_year {start_year} '\
                     f'--end_year {end_year}'
    return entrypoint

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
        self.key = f"results/multi_twist_model/{self.result_name}.csv"

        # run parameters
        self.scenario_type = self.model_config.get('scenario_type','historical')
        self.crop = self.model_config.get('crop','wheat')
        self.start_year = self.model_config.get('start_year',1975)
        self.end_year = self.model_config.get('end_year',2019)        
        self.shocked_region = self.model_config.get('shocked_region',None)
        self.shock_severity = self.model_config.get('shock_severity',None)
        self.scenario_start_year = self.model_config.get('scenario_start_year',None)

        # Docker commands
        self.entrypoint=gen_entrypoint(self.scenario_type, 
                                       self.start_year, 
                                       self.end_year, 
                                       self.crop, 
                                       shocked_region=self.shocked_region, 
                                       shock_severity=self.shock_severity, 
                                       scenario_start_year=self.scenario_start_year)
        self.volumes = { f"{self.config['TWIST']['OUTPUT_PATH']}/output_data": {'bind': '/output_data', 'mode': 'rw'},}

        # output locations
        self.output_base_path = f"{self.config['TWIST']['OUTPUT_PATH']}/output_data/world_market_price"
        self.output = gen_output_path(self.output_base_path, 
                                      self.scenario_type, 
                                      self.start_year, 
                                      self.end_year, 
                                      self.crop, 
                                      shocked_region=self.shocked_region, 
                                      shock_severity=self.shock_severity, 
                                      scenario_start_year=self.scenario_start_year)

        self.success_msg = 'Model run completed'
        self.descriptions = load_yaml("../metadata/models/multi-twist-model-metadata.yaml")

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=self.config['REDIS']['HOST'],
                        port=self.config['REDIS']['PORT'],
                        db=self.config['REDIS']['DB'])
        
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
        desc = f"{self.name} run for {self.scenario_type} scenario with start year {self.start_year} and end year {self.end_year}"
        if self.scenario_type == 'production_failure_scenario':
            desc += f". Shock severity was set to {self.shock_severity} and the shocked region was {self.shocked_region}."

        logging.info("Storing metadata...")
        meta = Metadata(run_id=self.run_id, 
                        model=self.name,
                        run_label=f"{self.name}: {self.scenario_type}",
                        run_description=desc,
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
            # some multi_twist outputs will not be present depending on the scenario type
            # so first check
            if feature_name in df:
                logging.info(f"Storing point data output for {feature_name}...")
                cols_to_select = base_cols + [feature_name]
                df_ = df[cols_to_select] # generate new interim DF
                df_['feature_name'] = feature_name
                df_['feature_description'] = feature_description.split('.')[0]
                df_['feature_value'] = df_[feature_name]
                df_ = df_[base_cols + feature_cols]

                # perform bulk insert of entire geopandas DF
                db_session.bulk_insert_mappings(Output, df_.to_dict(orient="records"))
                db_session.commit()