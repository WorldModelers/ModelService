import connexion
import six

from openapi_server.models.io_file import IOFile  # noqa: E501
from openapi_server.models.io_request import IORequest  # noqa: E501
from openapi_server.models.model import Model  # noqa: E501
from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.query import Query  # noqa: E501
from openapi_server import util

import requests
import configparser

import mint_client
from mint_client.rest import ApiException

# Load MINT configurations
config = configparser.ConfigParser()
config.read('config.ini')
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
    api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_models(username=username)
        models = [m.id for m in api_response]
        return models
    except ApiException as e:
        return "Exception when calling ModelApi->get_models: %s\n" % e


def model_config_model_name_get(ModelName):  # noqa: E501
    """Obtain an example model configuration.

    Submit a model name and receive a model configuration for the given model. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: ModelConfig
    """
    # get model
    try:
        api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
        model = api_instance.get_model(ModelName, username=username)
        versions = [v['id'] for v in model.has_software_version]

        # for each model version, obtain configuration ids
        configuration_ids = []
        api_instance = mint_client.ModelversionApi(mint_client.ApiClient(configuration))
        for v in versions:
            version = api_instance.get_model_version(v, username=username)
            c_ids = [c.id for c in version.has_configuration]
            configuration_ids.extend(c_ids)

        # get configurations
        configurations = []
        api_instance = mint_client.ModelconfigurationApi(mint_client.ApiClient(configuration))
        for _id in configuration_ids:
            config = api_instance.get_model_configuraton(_id, username=username)
            configurations.append({'name': ModelName, 'config': config.to_dict()})

        return configurations

    except ApiException as e:
        return "Exception when calling MINT: %s\n" % e

def model_info_model_name_get(ModelName):  # noqa: E501
    """Get basic metadata information for a specified model.

    Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: Model
    """
    try:
        api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
        api_response = api_instance.get_model(ModelName, username=username)
        model = {
                'name': api_response.id,
                'description': api_response.description,
                'maintainer': '',
                'category': api_response.has_model_category,
                'versions': [v['id'] for v in api_response.has_software_version]
        }
        return model
    except ApiException as e:
        return "Exception when calling ModelApi->get_model: %s\n" % e


def model_io_post():  # noqa: E501
    """Obtain information on a given model&#39;s inputs or outputs.

    Submit a model name and receive information about the input or output files required by this model. # noqa: E501
    Note that this includes all inputs and all outputs for a given model, irrespective of the 
    configuration. In the future this could be subset to just a specific configuration.

    :param io_request: The name of a model and an IO type.
    :type io_request: dict | bytes

    :rtype: List[IOFile]
    """
    if connexion.request.is_json:
        io_request = IORequest.from_dict(connexion.request.get_json())  # noqa: E501
        name_ = io_request.name
        type_ = io_request.iotype

        try:
            # get model configuration ids
            api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
            model = api_instance.get_model(name_, username=username)
            versions = [v['id'] for v in model.has_software_version]
            

            # for each model version, obtain configuration ids
            configuration_ids = []
            api_instance = mint_client.ModelversionApi(mint_client.ApiClient(configuration))
            for v in versions:
                version = api_instance.get_model_version(v, username=username)
                c_ids = [c.id for c in version.has_configuration]
                configuration_ids.extend(c_ids)

            # get IO
            api_instance = mint_client.ModelconfigurationApi(mint_client.ApiClient(configuration))

            inputs_outputs = []
            if type_ == 'input':
                for config_id in configuration_ids:
                    api_response = api_instance.get_inputs_by_modelconfiguration(config_id, username=username)
                    for io in api_response:
                        io_ = util._parse_io(io, url, request_headers)
                        if io_:
                            inputs_outputs.append(io_)

            elif type_ == 'output':
                outputs = []
                for config_id in configuration_ids:
                    api_response = api_instance.get_outputs_by_modelconfiguration(config_id, username=username)
                    for io in api_response:
                        io_ = util._parse_io(io, url, request_headers)
                        if io_:
                            inputs_outputs.append(io_)
            return inputs_outputs

        except ApiException as e:
            return "Exception when calling MINT API: %s\n" % e


def search_post():  # noqa: E501
    """Search for a model, dataset, or variable

    Search for a model, dataset, or variable based on name or standard name # noqa: E501

    :param search_item: Search parameters
    :type search_item: dict | bytes

    :rtype: SearchResult
    """
    # TODO IMPLEMENT THIS
    if connexion.request.is_json:
        search_item = Query.from_dict(connexion.request.get_json())  # noqa: E501
        print(search_item)
    return search_item
