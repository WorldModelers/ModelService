import boto3
import os
import redis
import configparser
from hashlib import sha256
import json
from collections import OrderedDict

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

def gen_run(input_file, output, year):
    model_name = 'flood_index_model'
    model_config = {
                    'config': {
                        "year": year
                    },
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    print(model_config)
    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/flood_index_model/{output}"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
    # Upload file to S3
    print(f"Uploading {run_obj['key']}...")
    s3_bucket.upload_file(input_file, run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Create Redis object
    r.hmset(run_id, run_obj)


def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res    

if __name__ == "__main__":

    # Wipe runs for the model
    r.delete('flood_index_model')

    file_lookup = {'floodIndex-78318c49e3646c852483accdeb818081':2017
                    'floodIndex-1c014ca61fc333d133d2401374073494':2016
                    'floodIndex-3961fe71a70139a2b2e5ed6b6d182e15':2015
                    'floodIndex-0cfb68f31772caecb01bee5a65b4f045':2014
                    'floodIndex-fa3dec98034bcc82a593a13dd0e89b82':2013
                    'floodIndex-916386f3d55ab25c7db1f87412f230d4':2012
                    'floodIndex-ba82906887e217d8f2b39e0c3f484a4e':2011
                    'floodIndex-800d64cd6c045767e8b6df1f0cfc1b7b':2010
                    'floodIndex-12284f102e499a616ccd44256c316eb7':2009
                    'floodIndex-33d0562575aa85c2c16e176cfc38fe06':2008}

    for input_file, year in file_lookup.items():
        output = f"{input_file}.nc"
        gen_run(input_file, output, year)