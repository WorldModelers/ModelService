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

bucket = 'world-modelers'

def gen_run(year, output):
    model_name = 'world_population_africa'
    model_config = {
                    'config': {
                      "year": year,
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
     'config': model_config,
     'bucket': bucket,
     'key': f"results/world_population_africa/{output}"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
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
    r.delete('world_population_africa')

    years = [2000, 2005, 2010, 2015, 2020]

    for year in years:
        # Generate merged runs
        output = "world_population_africa_{}.tif".format(year)
        gen_run(year, output)
