import sys
import os
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

import pandas as pd
import geopandas as gpd
import numpy as np
import shapely.geometry
import json
import yaml
import configparser
import redis
import boto3
from datetime import datetime, timedelta
from collections import OrderedDict
from hashlib import sha256
import urllib.request
import shutil
import time
import glob

import random
from shapely.ops import cascaded_union
from shapely.geometry import Point

param_types = {'samples':'integer',
                'start_year': 'integer',
                'number_years': 'integer',
                'management_practice': 'string',
                'rainfall': 'float',
                'fertilizer': 'integer',
                'planting_start': 'string',
                'planting_end': 'string',
                'season': 'string',
                'planting_window_shift': 'integer',
                'crop': 'string'
                }

def get_mgmt(filename):
    if 'rf_highn' in filename.lower():
        return 'rf_highN'
    elif 'irrig' in filename.lower():
        return 'irrig'
    elif 'rf_0N' in filename.lower():
        return 'rf_0N'
    elif 'rf_lown' in filename.lower():
        return 'rf_lowN'
  
def gen_run_id(model_name, params):
    
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()

    return run_id

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res                                


##################################################
#### DATA PREPARATION AND PREPROCESSING STEPS ####
##################################################

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

profile = "wmuser"
bucket = "world-modelers"

session = boto3.Session(profile_name=profile)
s3 = session.resource("s3")
s3_client = session.client("s3")
s3_bucket= s3.Bucket(bucket)

with open('../metadata/models/DSSAT-model-metadata.yaml', 'r') as stream:
    dssat = yaml.safe_load(stream)
    
model_name = dssat['id']    
##################################################
##################################################

if __name__ == "__main__":   

    baseline_runs = []
    for filename in glob.iglob('dssat_baseline_wheat/**/**.csv', recursive=True):
         baseline_runs.append(filename)

    sensitivity_runs = []
    for filename in glob.iglob('dssat_sensitivity_wheat/**/**.csv', recursive=True):
         sensitivity_runs.append(filename)         

    all_runs = {'baseline': baseline_runs, 'sensitivity': sensitivity_runs}
    
    #### PROCESS BASELINE RUNS ####
    ###############################
    for run_type, runs in all_runs.items():
        for filename in runs:
            print(f"Processing {run_type} {filename}")
            if 'belg' in filename.lower():
                season = "Belg"
            elif 'meher' in filename.lower():
                season = "Meher"

            management_practice = get_mgmt(filename)
            start_year = 2007
            samples = 0
            number_years = 10
            crop = 'wheat'

            if run_type == 'baseline':
                rainfall = 1
                fertilizer = 100
                planting_window_shift = 0
            else:
                # we need to extract this information from the filename
                fertilizer = int(filename.split("fen_tot")[1].split("_")[0])
                rainfall = float(filename.split("erain")[1].split("_")[0])
                planting_window_shift = int(filename.split("pfrst")[1].split("/")[0])


            params = {'samples': samples,
                      'start_year': start_year,
                      'number_years': number_years,
                      'management_practice': management_practice,
                      'rainfall': rainfall,
                      'fertilizer': fertilizer,
                      'season': season,
                      'planting_window_shift': planting_window_shift,
                      'crop': crop}

            run_id = gen_run_id(model_name, params)

            print(run_id, rainfall)
            # update row to database
            row = db_session.query(Parameters)\
                .filter(Parameters.run_id == run_id)\
                .filter(Parameters.parameter_name == 'rainfall')\
                .first()

            row.parameter_value = float(rainfall)
            db_session.commit()