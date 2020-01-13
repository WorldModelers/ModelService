import sys
import os
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

import pandas as pd
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

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res

def generate_impact_level(row):
    if row.dR == 0 and row.dC == 0:
        return 0 #"No Impact"
    elif row.dR < 0 and abs(row.dR)<row.R0 and row.dC==0:
        return 1 #"Low Impact"
    elif (row.R0 + row.dR) == 0 and (row.dR + row.dC)/row.S0 > -0.01:
        return 2 #"Medium Impact"
    elif (row.R0 + row.dR) == 0 and (row.dR + row.dC)/row.S0 < -0.01:
        return 3 #"Serious Impact"

def gen_run(model_name, params, input_file):
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    print(run_id)
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
    
    # Upload file to S3
    print(f"Uploading {run_obj['key']}...")
    s3_bucket.upload_file(input_file, run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config  

def ingest2db(df_, fsc, params, run_id, model_name):

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/{model_name}_results/{run_id}.csv",
                    run_label=f"{model_name} run for {params['shocked_region']} region.",
                    point_resolution_meters=100000)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    for pp, vv in params.items():
        param = Parameters(run_id=run_id,
                          model=model_name,
                          parameter_name=pp,
                          parameter_value=vv,
                          parameter_type="string"
                          )
        db_session.add(param)
        db_session.commit()    

    # Ingest outputs to DB
    feature_name = fsc['outputs'][0]['name']
    feature_description = fsc['outputs'][0]['description']
    df_['datetime'] = datetime(year=2018, month=1, day=1)
    df_['run_id'] = run_id
    df_['model'] = model_name
    df_['feature_description'] = feature_description
    df_['feature_value'] = df_[feature_name]

    db_session.bulk_insert_mappings(Output, df_.to_dict(orient="records"))
    db_session.commit()         

if __name__ == "__main__":
    init_db()
    with open('../metadata/models/FSC-model-metadata.yaml', 'r') as stream:
        fsc = yaml.safe_load(stream)

    model_name = fsc['id']

    df = pd.read_csv('FSC.csv')
    df = df[['P0','R0','dR','dC','S0','Region','Shock','Country']]
    df = df.rename(columns={'Region': "shocked_region", "Shock": "shock_severity", "Country": "country"})
    df = df.replace('MBBF','ALL')
    df['impact_level'] = df.apply(lambda row: generate_impact_level(row),axis=1)
    df = df[['country','shocked_region','shock_severity','impact_level']]
    df['crop'] = 'wheat'
    df = df.dropna()

    shock_regions = [i for i in fsc['parameters'] if i['name'] == 'shocked_region'][0]
    regions = shock_regions['metadata']['choices']

    for region in regions:
        params = {"crop": "wheat", "shocked_region": region}
        df_ = df[df['shocked_region'] == region]
        df_.to_csv("tmp.csv", index=False)
        run_id, model_config = gen_run(model_name, params, "tmp.csv")
        ingest2db(df_, fsc, params, run_id, model_name)