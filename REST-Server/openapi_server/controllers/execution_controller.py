import connexion
import six

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.run_results import RunResults  # noqa: E501
from openapi_server.models.run_status import RunStatus  # noqa: E501
from openapi_server import util
from openapi_server.kimetrica import KiController
from openapi_server.fsc import FSCController

import json
from hashlib import sha256
import docker
import configparser
import redis
import boto3
import botocore
import logging
logging.basicConfig(level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

client = docker.from_env()
containers = client.containers

available_models = ['malnutrition_model', 'fsc']

def list_runs_model_name_get(ModelName):  # noqa: E501
    """Obtain a list of runs for a given model

    Submit a &#x60;ModelName&#x60; and receive an array of &#x60;RunID&#x60;s associated with the given model. # noqa: E501

    :param model_name: A model name
    :type model_name: str

    :rtype: List[str]
    """
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

        if model_name.lower() not in available_models:
            return 'Model Not Found', 404, {'x-error': 'not found'}

        # generate id for the model run
        run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()

        if model_name.lower() == 'malnutrition_model':
            # run the model        
            model_config['config']['run_id'] = run_id
            kc = KiController(model_config)
            model_container = kc.run_model()
            stored = 1 # use binary for Redis
            m = kc

        elif model_name.lower() == 'fsc':
            model_config['config']['run_id'] = run_id
            fsc = FSCController(model_config['config'], config['FSC']['OUTPUT_PATH'])
            model_container = fsc.run_model()
            stored = 0 # use binary for Redis
            m = fsc

        # push the id to the model's list of runs
        r.sadd(model_name, run_id)

        # generate a key for the model run based on the run_id
        run_obj = {'config': json.dumps(model_config['config']),
                   'status': 'PENDING',
                   'container': model_container.id,
                   'bucket': m.bucket,
                   'key': m.key,
                   'stored': stored,
                   'name': model_config['name']}
        r.hmset(run_id, run_obj)        

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
        
    update_run_status(RunID)
    run = r.hgetall(RunID)
    status = run[b'status'].decode('utf-8')
    config = json.loads(run[b'config'].decode('utf-8'))
    model_name = run[b'name'].decode('utf-8')
    output = ''
    output_config = {'config': config, 'name': model_name}
    results = {'status': status, 'config': output_config, 'output': output}

    if status == 'SUCCESS':
        bucket = run[b'bucket'].decode('utf-8')
        key = run[b'key'].decode('utf-8')
        URI = f"https://s3.amazonaws.com/{bucket}/{key}"
        results['output'] = URI
        return results
    elif status == 'FAIL':
        run_container = run[b'container']
        run_logs = run_container.logs().decode('utf-8')
        results['output'] = run_logs
    print(results)
    return results


def run_status_run_idget(RunID):  # noqa: E501
    """Obtain status for a given model run

    Submit a &#x60;RunID&#x60; and receive the model run status # noqa: E501

    :param run_id: The &#x60;ID&#x60; for a given model run.
    :type run_id: str

    :rtype: RunStatus
    """
    return update_run_status(RunID)


def update_run_status(RunID):
    if not r.exists(RunID):
        return 'Run Not Found', 404, {'x-error': 'not found'}

    run = r.hgetall(RunID)
    run_container_id = run[b'container'].decode('utf-8')
    model_name = run[b'name'].decode('utf-8')
    
    model_container = containers.get(run_container_id)
    model_container.reload()
    container_status = model_container.status    


    run_logs = model_container.logs().decode('utf-8')
    conf = json.loads(run[b'config'].decode('utf-8'))
    print(run_logs)
    # if Kimetrica malnutrition model
    if model_name.lower() == 'malnutrition_model':
        success_msg = 'Model run: SUCCESS'

    # if FSC model
    elif model_name.lower() == 'fsc':
        success_msg = 'Output files stored to'

    status = 'PENDING'
    if container_status == 'exited':
        if success_msg in run_logs:
            # if FSC we need to ensure results are stored to S3
            # since Kimetrica model handles this within Docker directly
            try:
                store_results(RunID)
            except:
                return 'ERROR'

            r.hmset(RunID, {'status': 'SUCCESS'})
            status = 'SUCCESS'
        else:
            r.hmset(RunID, {'status': 'FAIL'})
            status = 'FAIL'
    return status


def store_results(RunID):
    run = r.hgetall(RunID)
    key = run[b'key'].decode('utf-8')
    bucket = config['S3']['BUCKET']
    model_config = json.loads(run[b'config'].decode('utf-8'))

    # check if S3 key exists
    s3 = boto3.resource('s3')
    try:
        s3.Object(bucket, key).load()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            # The object does not exist.
            try:
                fsc = FSCController(model_config, config['FSC']['OUTPUT_PATH'])
                fsc.storeResults() 
            except Exception as e:
                logging.error(e)
        else:
            logging.error('ERROR')
    else:
        # Key exists, do nothing
        logging.info('Results already stored to S3')    
