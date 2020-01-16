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
import time

import random
from shapely.ops import cascaded_union
from shapely.geometry import Point

def num(s):
    stringified = str(s)
    try:
        if '.' in stringified:
            return float(s)    
        else:
            return int(s)
    except:
        return s

def format_params(params_):
    
    # For historical: remove NAN values for these three parameters
    # Otherwsie format cereal_prodn_pctile (as float)
    if not pd.isna(params_['climate_anomalies']):
            params_['cereal_prodn_pctile'] = num(params_['cereal_prodn_pctile'])
    else:
        params_.pop('climate_anomalies')
        params_.pop('cereal_prodn_pctile')
        params_.pop('cereal_prodn_tercile')
     # floats
    params_['irrigation'] = num(params_['irrigation'])
    params_['additional_extension'] = num(params_['additional_extension'])
    params_['temperature'] = num(params_['temperature'])
    params_['rainfall'] = num(params_['rainfall'])

    # ints
    params_['sowing_window_shift'] = num(params_['sowing_window_shift'])
    params_['fertilizer'] = num(params_['fertilizer'])    
    return params_

def gen_run(model_name, params):
    params_ = {}
    for param in apsim['parameters']:
        try:
            params_[param['name']] = params[param['name']]
        except:
            # this is for the LT scenarios where some parameters are missing/null
            pass

    model_config = {
                    'config': params_,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()

    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/{model_name}_results/{run_id}.csv"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config, run_obj

def check_run_in_redis(model_name,scenarios,scen,crop_type,season_type):
    # obtain scenario parameters
    params = scenarios[scenarios['scenario']==scen].iloc[0].to_dict()
    params['crop'] = crop_type
    params['season'] = season_type
    params = format_params(params)

    params_ = {}
    for param in apsim['parameters']:
        try:
            params_[param['name']] = params[param['name']]
        except:
            # this is for the LT scenarios where some parameters are missing/null
            pass
    
    model_config = {
                    'config': params_,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()    

    # Check if run in Redis
    return r.sismember(model_name, run_id), run_id

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res                                

def process_crops_(crops_, scen, crop_type, season_type, scenarios, apsim):
    """
    Primary function for processing each crop type/season/scenario combo
    """

    # subset for the correct scenario
    crops_ = crops_[crops_['scenario'] == scen]

    crops_['geometry'] = crops_.apply(lambda x: Point(x.longitude, x.latitude), axis=1)

    # obtain scenario parameters
    params = scenarios[scenarios['scenario']==scen].iloc[0].to_dict()
    params['crop'] = crop_type
    params['season'] = season_type
    params = format_params(params)

    run_id, model_config, run_obj = gen_run(model_name, params)

    # generate temp CSV and push it to S3
    crops_.to_csv("tmp.csv", index=False)
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
                    run_label=crops_.description.iloc[0],
                    point_resolution_meters=25000)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    for param in apsim['parameters']:
        # ensure that no null parameters are stored
        try:
            if param['metadata']['type'] == 'ChoiceParameter':
                p_type = 'string'
            elif param['name'] == 'fertilizer' or param['name'] == 'sowing_window_shift':
                p_type = 'int'
            else:
                p_type = 'float'
            p_value = params[param['name']]

            param = Parameters(run_id=run_id,
                              model=model_name,
                              parameter_name=param['name'],
                              parameter_value=p_value,
                              parameter_type=p_type
                              )
            db_session.add(param)
            db_session.commit()
        except:
            # skip LT parameters
            pass
        
    gdf = gpd.GeoDataFrame(crops_)
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

scenarios = pd.read_csv('Scenarios.csv')
grids = pd.read_csv('Experiment 2020-01 - Gridcell Centre Points.csv')

with open('../metadata/models/APSIM-model-metadata.yaml', 'r') as stream:
    apsim = yaml.safe_load(stream)

admin2 = gpd.read_file("gadm36_ETH_shp/gadm36_ETH_2.shp")
admin2['country'] = admin2['NAME_0']
admin2['state'] = admin2['NAME_1']
admin2['admin1'] = admin2['NAME_1']
admin2['admin2'] = admin2['NAME_2']
admin2['GID_2'] = admin2['GID_2'].apply(lambda x: x.split("_")[0])
admin2['GID_1'] = admin2['GID_1'].apply(lambda x: x.split("_")[0])

eth = cascaded_union(admin2.geometry)

# download APSIM files
print("Downloading APSIM files...")
urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/CSIRO/APSIM_Backcast.csv", "APSIM_Backcast.csv")
urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/CSIRO/APSIM_LT_Historical.csv", "APSIM_LT_Historical.csv")
print("Download complete!")

crops = pd.read_csv('APSIM_Backcast.csv')
crops_lt = pd.read_csv('APSIM_LT_Historical.csv')

# obtain lat/lon from grid file
crops = crops.merge(grids, how='left', left_on='gridcell_id', right_on='CellId')
crops_lt = crops_lt.merge(grids, how='left', left_on='gridcell_id', right_on='CellId')

# add in parameters from scenarios dataframe
crops = crops.merge(scenarios, on='scenario', how='left', suffixes=(False, False))

crops_lt = crops_lt.merge(scenarios, on='scenario', how='left', suffixes=(False, False))

model_name = apsim['id']
crop_param = [i for i in apsim['parameters'] if i['name']=='crop'][0]
season_param = [i for i in apsim['parameters'] if i['name']=='season'][0]

outputs = {}
for o in apsim['outputs']:
    outputs[o['name']] = o
    
scenario_list = crops.scenario.unique()
scenario_list_lt = crops_lt.scenario.unique()

param_cols = list(scenarios.columns)
base_cols = ['gridcell_id', 'cropping_year','latitude','longitude']
base_cols_lt = ['gridcell_id','latitude','longitude']

##################################################
##################################################

if __name__ == "__main__":

    for c_ in [crops, crops_lt]:
        if 'non_temporal' in c_:
            print("Processing LT historical...")
            scen_list_ = scenario_list_lt
            b_cols = base_cols_lt
        else:
            print("Processing backcasting...")
            scen_list_ = scenario_list
            b_cols = base_cols
        # process backcast results
        for season_type in season_param['metadata']['choices']:
            
            for crop_type in crop_param['metadata']['choices']:

                for scen in scen_list_:

                    # Ensure run not in Redis:
                    run_in_redis, run_id = check_run_in_redis(model_name,scenarios,scen,crop_type,season_type)

                    # if run is not in Redis, process it
                    if not run_in_redis:
                        # select the correct yield columns for crop/season and rename them
                        area_col = f"season_area_{crop_type}_{season_type}"
                        production_col = f"season_prodn_{crop_type}_{season_type}"
                        yield_col = f"season_mean_yield_{crop_type}_{season_type}"
                        production_anomaly = f"season_rel_prodn_quintal_anomaly_{crop_type}_{season_type}"
                        yield_anomaly  = f"season_rel_mean_yield_anomaly_{crop_type}_{season_type}"
                        cols = param_cols + b_cols + [area_col, production_col, yield_col, production_anomaly, yield_anomaly]
                        crops_ = c_[cols]
                        crops_ = crops_.rename(columns={area_col: 'area',
                                                        production_col: 'production',
                                                        yield_col:'yield',
                                                        production_anomaly: 'production_anomaly',
                                                        yield_anomaly:'yield_anomaly'})

                        if 'cropping_year' in crops_:
                            crops_['datetime'] = crops_.cropping_year.apply(lambda x: datetime(year=x,month=1,day=1))
                        
                        # subset for the correct scenario
                        crops_ = crops_[crops_['scenario'] == scen]
                        
                        # drop rows where yield fields are NA
                        crops_ = crops_.dropna(subset=['area','production','yield','production_anomaly','yield_anomaly'])
                        
                        gdf, run_id = process_crops_(crops_, scen, crop_type, season_type, scenarios, apsim)

                        print(f"Processing {crop_type} for {season_type} season with run_id {run_id}")
                            
                        for feature in ['area','production','yield','production_anomaly','yield_anomaly']:
                            gdf_ = gdf
                            gdf_['feature_name'] = feature
                            gdf_['feature_value'] = gdf_[feature]
                            gdf_['feature_description'] = outputs[feature]['description']
                            
                            db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
                            db_session.commit()    

                    else: 
                        print(f"Run {run_id} already in Redis for scenario {scen}")