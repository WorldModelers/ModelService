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
from datetime import datetime
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

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def get_mgmt(filename):
    if 'rf_highn' in filename.lower():
        return 'maize_rf_highN'
    elif 'irrig' in filename.lower():
        return 'maize_irrig'
    elif 'rf_0N' in filename.lower():
        return 'maize_rf_0N'
    elif 'rf_lown' in filename.lower():
        return 'maize_rf_lowN'

def gen_run(model_name, params):
    
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config, cls=NpEncoder).encode('utf-8')).hexdigest()

    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/{model_name}_results/{run_id}.csv"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'], cls=NpEncoder)
    
    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config, run_obj
      

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res                                

def process_dssat(df, params, dssat, model_name):
    """
    Primary function for processing DSSAT
    """

    run_id, model_config, run_obj = gen_run(model_name, params)

    # generate temp CSV and push it to S3
    df.to_csv("tmp.csv", index=False)
    time.sleep(1)
    try:
        s3_bucket.upload_file("tmp.csv", run_obj['key'], ExtraArgs={'ACL':'public-read'})
    except Exception as e:
        print(e)
        print("Retrying file upload...")
        try:
            s3_bucket.upload_file("tmp.csv", run_obj['key'], ExtraArgs={'ACL':'public-read'})
        except:
            pass

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/{model_name}_results/{run_id}.csv",
                    run_label=df.RUN_NAME.iloc[0],
                    point_resolution_meters=10000)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    for p_name, p_value in params.items():
        param = Parameters(run_id=run_id,
                          model=model_name,
                          parameter_name=p_name,
                          parameter_value=p_value,
                          parameter_type=param_types[p_name]
                          )
        db_session.add(param)
        db_session.commit()
        
    gdf = gpd.GeoDataFrame(df)
    gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
    gdf['run_id'] = run_id
    gdf['model'] = model_name
    if 'geometry' in gdf:
        del(gdf['geometry'])
        del(gdf['index_right'])
        
    return gdf, run_id


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

admin2 = gpd.read_file("../CSIRO-Integration/gadm36_ETH_shp/gadm36_ETH_2.shp")
admin2['country'] = admin2['NAME_0']
admin2['state'] = admin2['NAME_1']
admin2['admin1'] = admin2['NAME_1']
admin2['admin2'] = admin2['NAME_2']
admin2['GID_2'] = admin2['GID_2'].apply(lambda x: x.split("_")[0])
admin2['GID_1'] = admin2['GID_1'].apply(lambda x: x.split("_")[0])

eth = cascaded_union(admin2.geometry)

model_name = dssat['id']

outputs = {}
for o in dssat['outputs']:
    outputs[o['name']] = o
    
##################################################
##################################################

if __name__ == "__main__":

    # download DSSAT files
    # print("Downloading DSSAT basline file...")
    # urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/DSSAT/ETH_ALL_Maize_baseline.tar.xz", "dssat_baseline.tar.xz")

    # print("Unpacking DSSAT basline files...")
    # shutil.unpack_archive("dssat_baseline.tar.xz", "dssat_baseline")

    # print("Downloading DSSAT sensitivity file...")
    # urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/DSSAT/ETH_Oroima_Maize_global_sens.tar.xz", "dssat_sensitivity.tar.xz")

    # print("Unpacking DSSAT sensitivity files...")
    # shutil.unpack_archive("dssat_sensitivity.tar.xz", "dssat_sensitivity")    

    baseline_runs = []
    for filename in glob.iglob('dssat_baseline/**/**.csv', recursive=True):
         baseline_runs.append(filename)

    sensitivity_runs = []
    for filename in glob.iglob('dssat_sensitivity/**/**.csv', recursive=True):
         sensitivity_runs.append(filename)         

    all_runs = {'baseline': baseline_runs, 'sensitivity': sensitivity_runs}

    #### PROCESS BASELINE RUNS ####
    ###############################
    for run_type, runs in all_runs.items():
        print(f"Processing {run_type} runs...")
        for run in runs:
            print(f"Processing {run_type} {run}")
            if 'BELG' in run:
                management_practice = get_mgmt(filename)
                season = "Belg"
            elif 'MEHER' in run:
                management_practice = get_mgmt(filename)
                season = "Meher"

            start_year = 1984
            samples = 0
            number_years = 35
            crop = 'maize'

            if run_type == 'baseline':
                rainfall = 1
                fertilizer = 100
                planting_window_shift = 0
            else:
                # we need to extract this information from the filename
                fertilizer = int(filename.split("fentot")[1].split("_")[0])
                rainfall = float(filename.split("erain")[1].split("_")[0])
                planting_window_shift = int(filename.split("pfirst")[1].split(".csv")[0])


            params = {'samples': samples,
                          'start_year': start_year,
                          'number_years': number_years,
                          'management_practice': management_practice,
                          'rainfall': rainfall,
                          'fertilizer': fertilizer,
                          'season': season,
                          'planting_window_shift': planting_window_shift,
                          'crop': crop}

            df = pd.read_csv(run)
            df['geometry'] = df.apply(lambda x: Point(x.LONGITUDE, x.LATITUDE), axis=1)
            df['Yield'] = df['HWAH'] * df['HARVEST_AREA']

            gdf, run_id = process_dssat(df, params, dssat, model_name)
                
            for feature in ['Yield','HARVEST_AREA','HWAH']:
                gdf_ = gdf
                gdf_['feature_name'] = feature
                gdf_['feature_value'] = gdf_[feature]
                gdf_['feature_description'] = outputs[feature]['description']
                
                db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
                db_session.commit()    