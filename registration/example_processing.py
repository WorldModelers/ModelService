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

def get_type(x):
    if type(x) == int:
        return 'integer'
    elif type(x) == float:
        return 'float'
    else:
        return 'string'

def gen_run(model_name, params, file):
    
    model_config = {
                    'config': params,
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
     'key': f"results/{model_name}_results/{file}"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
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

def process(df, params, m, model_name, file):
    """
    Primary function for processing DSSAT
    """

    run_id, model_config, run_obj = gen_run(model_name, params, file)

    try:
        s3_bucket.upload_file(file, run_obj['key'], ExtraArgs={'ACL':'public-read'})
    except Exception as e:
        print(e)
        print("Retrying file upload...")
        try:
            s3_bucket.upload_file(file, run_obj['key'], ExtraArgs={'ACL':'public-read'})
        except:
            pass

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/{model_name}_results/{file}",
                    run_label=f"Run for {model_name}",
                    point_resolution_meters=m.get("point_resolution_meters",1000))
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    for p_name, p_value in params.items():
        param = Parameters(run_id=run_id,
                          model=model_name,
                          parameter_name=p_name,
                          parameter_value=p_value,
                          parameter_type=get_type(p_value)
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

admin2 = gpd.read_file("../shapes/gadm36_ETH_shp/gadm36_ETH_2.shp")
admin2['country'] = admin2['NAME_0']
admin2['state'] = admin2['NAME_1']
admin2['admin1'] = admin2['NAME_1']
admin2['admin2'] = admin2['NAME_2']
admin2['GID_2'] = admin2['GID_2'].apply(lambda x: x.split("_")[0])
admin2['GID_1'] = admin2['GID_1'].apply(lambda x: x.split("_")[0])

    
##################################################
##################################################

if __name__ == "__main__":  
    run_path = sys.argv[1]
    metadata = sys.argv[2]

    with open(metadata, 'r') as stream:
        m = yaml.safe_load(stream)    

    model_name = m['id']
    
    outputs = {}
    for o in m['outputs']:
        outputs[o['name']] = o    

    files = glob.glob(f"{run_path}/*.csv")
    
    for file in files:
        print(f"Ingesting file {file}...")
        df = pd.read_csv(file)
        df['geometry'] = df.apply(lambda x: Point(x.longitude, x.latitude), axis=1)

        # Generate parameter dictionary
        param_cols = [i['name'] for i in m['parameters']]
        params = {}
        for p in param_cols:
            params[p] = df[p].iloc[0]

        gdf, run_id = process(df, params, m, model_name, file)
            
        for kk, vv in outputs.items():
            gdf_ = gdf
            gdf_['feature_name'] = kk
            gdf_['feature_value'] = gdf_[kk]
            gdf_['feature_description'] = vv['description']
            
            db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
            db_session.commit()