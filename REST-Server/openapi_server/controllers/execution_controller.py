import connexion
import six

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.run_results import RunResults  # noqa: E501
from openapi_server.models.run_status import RunStatus  # noqa: E501
from openapi_server import util
from openapi_server.kimetrica import KiController, get_model_runs

import json
from hashlib import sha256
import docker
import configparser
import redis

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

client = docker.from_env()
containers = client.containers

def list_runs_model_name_get(ModelName):  # noqa: E501
    """Obtain a list of runs for a given model

    Submit a &#x60;ModelName&#x60; and receive an array of &#x60;RunID&#x60;s associated with the given model. # noqa: E501

    :param model_name: A model name
    :type model_name: str

    :rtype: List[str]
    """
    runs = get_model_runs(ModelName)
    return runs


def run_model_post(model_config):  # noqa: E501
    """Run a model for a given a configuration

    Submit a configuration to run a specific model. Model is run asynchronously. Results are available through &#x60;/run_results&#x60; endpoint. # noqa: E501

    :param model_config: Model and configuration parameters
    :type model_config: dict | bytes

    :rtype: str
    """
    if connexion.request.is_json:
        model_config = ModelConfig.from_dict(connexion.request.get_json())  # noqa: E501

        kc = KiController()
        model_container = kc.run_model()

        run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
        run_obj = {'model_config': model_config,
                   'status': 'PENDING',
                   'container': model_container.id,
                   'bucket': kc.bucket,
                   'key': kc.key}
        r.hmset(run_id, run_obj)        

    return run_id


def run_results_run_idget(run_id):  # noqa: E501
    """Obtain metadata about the results of a given model run

    Submit a &#x60;RunID&#x60; and receive model run results metadata, including whether it succeeded or failed and where to access the result data. # noqa: E501

    :param run_id: The ID for a given model run.
    :type run_id: str

    :rtype: RunResults
    """
    run = r.hgetall(run_id)
    status = run[b'status'].decode('utf-8')
    if status == 'SUCCESS':
        bucket = run[b'bucket'].decode('utf-8')
        key = run[b'key'].decode('utf-8')
        URI = f"https://s3.amazonaws.com/{bucket}/{key}"
        results = {'status': status, 'URI': URI}
        return results
    elif status == 'FAIL':
        run_container = run[b'container']
        run_logs = run_container.logs().decode('utf-8')
        results = {'status': status, 'logs': run_logs}
    else:
        results = {'status': status}


def run_status_run_idget(run_id):  # noqa: E501
    """Obtain status for a given model run

    Submit a &#x60;RunID&#x60; and receive the model run status # noqa: E501

    :param run_id: The &#x60;ID&#x60; for a given model run.
    :type run_id: str

    :rtype: RunStatus
    """
    run = r.hgetall(run_id)
    run_container = run[b'container']
    run_container.reload()
    container_status = run_container.status

    model_container = containers.get(run_container)
    success_msg = 'Model run: SUCCESS'
    fail_msg = 'Model run: FAIL'
    run_logs = model_container.logs().decode('utf-8')

    status = 'PENDING'
    if container_status == 'exited':
        if success_msg in run_logs:
            r.hmset('testid', {'status': 'SUCCESS'})
            status = 'SUCCESS'
        elif success_msg in run_logs:
            r.hmset('testid', {'status': 'FAIL'})
            status = 'FAIL'

    return status