import connexion
import six

from openapi_server.models.io_file import IOFile  # noqa: E501
from openapi_server.models.io_request import IORequest  # noqa: E501
from openapi_server.models.model import Model  # noqa: E501
from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.query import Query  # noqa: E501
from openapi_server.models.geo_query import GeoQuery  # noqa: E501
from openapi_server.models.text_query import TextQuery  # noqa: E501
from openapi_server.models.time_query import TimeQuery  # noqa: E501
from openapi_server import util
from openapi_server import metadata

import requests
import configparser
import json
import redis

# Initialize metadata
metadata.main()

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

# Load MINT configurations
import mint_client
from mint_client.rest import ApiException

url = config['MINT']['URL']
provenance_id = config['MINT']['PROVENANCE_ID']
username = config['MINT']['USERNAME']
password = config['MINT']['PASSWORD']

# Authenticate with MINT Model Catalog (MCAT)
configuration = mint_client.Configuration()
api_instance = mint_client.UserApi()
user = mint_client.User(username=username, password=password)

# Authenticate with MINT Data Catalog (DCAT)
resp = requests.get(f"{url}/get_session_token").json()
api_key = resp['X-Api-Key']

# Set DCAT request headers
request_headers = {
    'Content-Type': "application/json",
    'X-Api-Key': api_key
}

try:
    # Logs user into MINT
    configuration.access_token = api_instance.login_user(username, password)
    print("Log in success! Token: %s\n" % configuration.access_token)
except ApiException as e:
    print("Exception when calling UserApi->login_user: %s\n" % e)    

def list_models_post():  # noqa: E501
    """Obtain a list of current models

    Request a list of currently available models. # noqa: E501


    :rtype: List[str]
    """
    m_ids = [m.decode('utf-8') for m in r.smembers('model-list')]
    
    models = []

    for _id in m_ids:
        m = json.loads(r.get(f"{_id}-meta").decode('utf-8'))
        models.append(util.format_model(m))

    return models

def model_config_model_name_get(ModelName):  # noqa: E501
    """Obtain an example model configuration.

    Submit a model name and receive a model configuration for the given model. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: ModelConfig
    """
    # get model
    m = json.loads(r.get(f'{ModelName}-meta').decode('utf-8'))
    return util.format_config(m)

def model_info_model_name_get(ModelName):  # noqa: E501
    """Get basic metadata information for a specified model.

    Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: Model
    """
    m = json.loads(r.get(f'{ModelName}-meta').decode('utf-8'))
    return util.format_model(m)


def model_outputs_model_name_get(ModelName):  # noqa: E501
    """Obtain information on a given model&#39;s outputs.

    Submit a model name and receive information about the output variables produced by this model. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: List[Variable]
    """
    m = json.loads(r.get(f'{ModelName}-meta').decode('utf-8'))
    return util.format_outputs(m)


def model_parameters_model_name_get(ModelName):  # noqa: E501
    """Obtain information about a model&#39;s parameters.

    Submit a model name and receive information about the parameters used by this model. Specific parameters are used on a per-configuration basis. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: List[Parameter]
    """

    # Obtain all parameters associated with *any* configuration for 
    # the given model
    m = json.loads(r.get(f'{ModelName}-meta').decode('utf-8'))
    return util.format_parameters(m)