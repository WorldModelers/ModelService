import psycopg2
import requests
import configparser
import json
import redis
import sys


config = configparser.ConfigParser()
config.read('./config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

con = psycopg2.connect(database=config["DATABASE"]["DB"], user=config["DATABASE"]["USER"], password=config["DATABASE"]["PASSWORD"], host=config["DATABASE"]["URL"], port=config["DATABASE"]["PORT"])
cur = con.cursor()

print("Database opened successfully")

def delete_all_model_data(cur,model):
    cur.execute(f"DELETE FROM OUTPUT WHERE MODEL = '{model}';")
    cur.execute(f"DELETE FROM PARAMETERS WHERE MODEL = '{model}';")
    cur.execute(f"DELETE FROM METADATA WHERE MODEL = '{model}';")
    con.commit()
    return

def delete_by_run_id(cur,run_id):
    cur.execute(f"DELETE FROM OUTPUT WHERE RUN_ID = '{run_id}';")
    cur.execute(f"DELETE FROM PARAMETERS WHERE RUN_ID = '{run_id}';")
    cur.execute(f"DELETE FROM METADATA WHERE RUN_ID = '{run_id}';")
    con.commit()
    return

def delete_model_run_data_from_redis(ModelName):
    if ModelName.lower() in ['fsc','dssat','chirps','chirps-gefs']:
        ModelName = ModelName.upper()

    if not r.exists(ModelName):
        return
    else:
        runs = [run.decode('utf-8') for run in list(r.smembers(ModelName))]

    for RunID in runs:
        r.srem(ModelName,RunID)
        run = r.hgetall(RunID)
        if run == {}:
            continue
        r.delete(RunID)


MODEL = sys.argv[1]

delete_model_run_data_from_redis(MODEL)
delete_all_model_data(cur,MODEL)
con.close()
