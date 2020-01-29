import connexion
import six
import flask

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.run_results import RunResults  # noqa: E501
from openapi_server.models.run_status import RunStatus  # noqa: E501
from openapi_server import util
from openapi_server.kimetrica import KiController, run_kimetrica
from openapi_server.fsc import FSCController, run_fsc
from openapi_server.dssat import DSSATController, run_dssat
from openapi_server.chirps import CHIRPSController, run_chirps
from openapi_server.twist import TWISTController, run_twist

import json
from hashlib import sha256
import docker
import configparser
import redis
from rq import Queue
import boto3
import botocore
import logging
import os
import glob
import yaml
import time
from collections import OrderedDict
from random import choice as randomchoice
logging.basicConfig(level=logging.INFO)

data_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
print(data_file_dir)

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

q = Queue('high', connection=r)

client = docker.from_env()
containers = client.containers

data_path = config['APP']['DATA_PATH']
site_url = config['APP']['URL']

metadata_files = []
for filename in glob.iglob('../metadata/models/**model-metadata.yaml', recursive=True):
     metadata_files.append(filename)

available_models = []
non_executable_models = []        

for m in metadata_files:
    with open(m, 'r') as stream:
        model = yaml.safe_load(stream)
        available_models.append(model['id'].lower())

        # check whether model is executable or not
        if model['executable'] == False:
            non_executable_models.append(model['id'].lower())


def list_runs_model_name_get(ModelName):  # noqa: E501
    """Obtain a list of runs for a given model

    Submit a &#x60;ModelName&#x60; and receive an array of &#x60;RunID&#x60;s associated with the given model. # noqa: E501

    :param model_name: A model name
    :type model_name: str

    :rtype: List[str]
    """
    if ModelName.lower() in ['fsc','dssat','chirps','chirps-gefs','pihm']:
        ModelName = ModelName.upper()

    if not r.exists(ModelName):
        return []
    else:
        runs = [run.decode('utf-8') for run in list(r.smembers(ModelName))]
        return runs


def run_model_post():  # noqa: E501
    """Run a model for a given a configuration

    Submit a configuration to run a specific model. Model is run asynchronously. Results are available through &#x60;/run_results&#x60; endpoint. # noqa: E501

    :param model_config: Model and configuration parameters
    :type model_config: dict | bytes

    :rtype: str
    """
    if connexion.request.is_json:
        model_config = ModelConfig.from_dict(connexion.request.get_json())  # noqa: E501
        model_config = model_config.to_dict()
        model_name = model_config["name"]
        
        model_config = util.sortOD(OrderedDict(model_config))

        # generate id for the model run
        run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()    

        # if run already exists and is success or pending, don't run again.
        if r.exists(run_id):
            run = r.hgetall(run_id)
            status = run[b'status'].decode('utf-8')
            if status == "SUCCESS" or status == "PENDING":
                logging.info("Already ran " + run_id)
                return run_id

        if model_name.lower() not in available_models:
            return 'Model Not Found', 404, {'x-error': 'not found'}

        # if non executable model, do nothing
        if model_name.lower() in non_executable_models:
            return f'{model_name} is not currently executable. Please refer to the available pre-computed results.', 400, {'x-error': 'not supported'}                

        # generate a key for the model run based on the run_id
        run_obj = {'config': json.dumps(model_config['config']),
                   'status': 'PENDING',
                   'name': model_config['name'],
                   'timestamp': round(time.time()*1000,0)}
        r.hmset(run_id, run_obj)

        # push the id to the model's list of runs
        r.sadd(model_name, run_id)

        if model_name.lower() == 'malnutrition_model' \
        or model_name.lower() == 'population_model': 
            model_config['config']['run_id'] = run_id
            q.enqueue(run_kimetrica, model_config, job_timeout='4h')            
            model_container = None
            m = KiController(model_config)

        elif model_name.lower() == 'fsc':
            model_config['config']['run_id'] = run_id
            q.enqueue(run_fsc, model_config['config'], config['FSC']['OUTPUT_PATH'])
            model_container = None
            m = FSCController(model_config['config'], config['FSC']['OUTPUT_PATH'])

        elif model_name.lower() == 'dssat':
            model_config['config']['run_id'] = run_id
            q.enqueue(run_dssat, model_config['config'], config['DSSAT']['OUTPUT_PATH'], job_timeout='12h')
            model_container = None
            m = DSSATController(model_config['config'], config['DSSAT']['OUTPUT_PATH'])

        elif 'chirps' in model_name.lower():
            model_config['config']['run_id'] = run_id
            q.enqueue(run_chirps, model_name, model_config['config'], config['CHIRPS']['OUTPUT_PATH'])
            model_container = None
            m = CHIRPSController(model_name, model_config['config'], config['CHIRPS']['OUTPUT_PATH'])

        elif 'multi_twist' in model_name.lower():
            model_config['config']['run_id'] = run_id
            q.enqueue(run_twist, model_config['config'])
            model_container = None
            m = TWISTController(model_config['config'])

    return run_id


def run_results_run_idget(RunID):  # noqa: E501
    """Obtain metadata about the results of a given model run

    Submit a &#x60;RunID&#x60; and receive model run results metadata, including whether it succeeded or failed and where to access the result data. # noqa: E501

    :param run_id: The ID for a given model run.
    :type run_id: str

    :rtype: RunResults
    """
    if not r.exists(RunID):
        return 'Run Not Found', 404, {'x-error': 'not found'}
        
    run = r.hgetall(RunID)
    status = run[b'status'].decode('utf-8')

    # Only update the run status if the status is still PENDING
    if status == 'PENDING':
        update_run_status(RunID)
        run = r.hgetall(RunID)
        status = run[b'status'].decode('utf-8')

    config = json.loads(run[b'config'].decode('utf-8'))
    if 'run_id' not in config:
        config['run_id'] = RunID
        
    model_name = run[b'name'].decode('utf-8')

    if b'output' not in run:
        output = ''
    else: # failed runs should have stored output
        output = run[b'output'].decode('utf-8')

    output_config = {'config': config, 'name': model_name}
    results = {'status': status, 
               'config': output_config, 
               'output': output, 
               'auth_required': False}
    
    if b'timestamp' in run:
        timestamp = run[b'timestamp'].decode('utf-8')
        results['timestamp'] = int(timestamp.split('.')[0])

    if model_name in ['consumption_model', 'asset_wealth_model']:
        # special handler for Atlas.ai models
        URI = f"{site_url}/result_file/{RunID}.{config['format']}"
        results['output'] = URI
        # ensure that auth_required is set to true
        results['auth_required'] = True
        return results 
    elif status == 'SUCCESS':
        bucket = run[b'bucket'].decode('utf-8')
        key = run[b'key'].decode('utf-8')
        URI = f"https://s3.amazonaws.com/{bucket}/{key}"
        results['output'] = URI
        return results
    elif status == 'FAIL':
        # do nothing as `output` is set by the model controllers
        # based on the specific error that occurred
        pass 
    return results


def run_status_run_idget(RunID):  # noqa: E501
    """Obtain status for a given model run

    Submit a &#x60;RunID&#x60; and receive the model run status # noqa: E501

    :param run_id: The &#x60;ID&#x60; for a given model run.
    :type run_id: str

    :rtype: RunStatus
    """
    return update_run_status(RunID)


def available_results_get(ModelName=None, size=None):
    """Obtain a list of run results

    Return a list of all available run results. # noqa: E501

    :rtype: List[RunResults]
    """
    model = ModelName

    if model != None:
        if model.lower() not in available_models:
            return 'Model Not Found', 404, {'x-error': 'not found'}

    run_ids = []

    # no model or size
    if model == None and size == None:
        for m in available_models:
            if m in ['fsc','dssat','chirps','chirps-gefs']:
                m = m.upper()
            runs = list_runs_model_name_get(m)
            run_ids.extend(runs)

    # model provided but no size
    elif model != None and size == None:
        runs = list_runs_model_name_get(model)
        run_ids.extend(runs)

    # size provided but no model
    elif model == None and size != None:
        n = 1
        while n <= size:
            m = randomchoice(available_models)
            if m in ['fsc','dssat','chirps','chirps-gefs']:
                m = m.upper()
            rand_run = r.srandmember(m)
            if rand_run != None:
                run_ids.append(rand_run.decode('utf-8'))
                n+=1

    # model provided and size provided
    elif model != None and size != None:
        runs = [run.decode('utf-8') for run in list(r.srandmember(model, size))]
        run_ids.extend(runs)

    results = []
    for id_ in run_ids:
        results.append(run_results_run_idget(id_))
    return results


def result_file_result_file_name_get(ResultFileName):  # noqa: E501
    """Obtain the result file for a given model run.

    Submit a &#x60;ResultFileName&#x60; and receive model run result file. # noqa: E501

    :param result_file_name: A file name of a result file.
    :type result_file_name: str

    :rtype: None
    """

    # If the file does not exist:
    if not os.path.exists(f"{data_path}/{ResultFileName}"):
        return 'Result File Not Found', 404, {'x-error': 'not found'}

    # Otherwise, serve the file:
    else:
        response = flask.send_from_directory(data_path, ResultFileName)  
        response.direct_passthrough = False
        return response    


def update_run_status(RunID):
    if not r.exists(RunID):
        return 'Run Not Found', 404, {'x-error': 'not found'}

    run = r.hgetall(RunID)
    return run[b'status'].decode('utf-8')
