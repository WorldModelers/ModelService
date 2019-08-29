import boto3
import os
import argparse
import redis
import configparser
from hashlib import sha256
import json

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

profile = "wmuser"
bucket_name = "world-modelers"
models = ['consumption_model','asset_wealth_model']
formats = ['tif','geojson']
atlas_lookup = {
               'asset_wealth_model':{
                  'geojson':'november_tests_asset_wealth.geojson',
                  'tif':'november_tests_atlasai_assetwealth_allyears_2km.tif'
               },
               'consumption_model':{
                  'geojson':'november_tests_consumption.geojson',
                  'tif':'november_tests_atlasai_consumption_allyears_2km.tif'
               }
            }

session = boto3.Session(profile_name=profile)

s3 = session.resource("s3")
s3_client = session.client("s3")

bucket = s3.Bucket(bucket_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Atlas.a Data Downloader')
    parser.add_argument('--output_directory', type=str,
                        help='Where should Atlas.ai data be downloaded?')
    parser.add_argument('--key_file', type=str,
                        help='A text file containing the S3 keys for the Atlas files.')

    args = parser.parse_args()
    output_directory = args.output_directory
    key_file = args.key_file

    keys = [i.split('\n')[0] for i in open(key_file).readlines()]

    # make Atlas.ai data directory
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
        print(f"Created {output_directory} directory.\n")

    # download files
    print("Downloading data files...")
    for k in keys:
        file_name = k.split('/')[-1]
        bucket.download_file(k, f"{output_directory}/{file_name}")
    print("...download completed!\n")

    # update redis with model run
    print("Updating Redis...")
    for model_name in models:
        for f in formats:
            model_config = {
              "config": {"format": f},
              "name": model_name
            }
            
            run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
            
            # Add to model set in Redis
            r.sadd(model_name, run_id)
            
            run_obj = {'status': 'SUCCESS',
             'name': model_name,
             'config': model_config["config"],
            }

            run_obj['config']['run_id'] = run_id
            run_obj['config'] = json.dumps(run_obj['config'])
            
            r.hmset(run_id, run_obj)
            
            # rename files to correspond with model run_id
            file_name = atlas_lookup[model_name][f]
            os.rename(f"{output_directory}/{file_name}", f"{output_directory}/{run_id}.{f}")
    print("...Redis update completed!")