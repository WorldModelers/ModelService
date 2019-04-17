import connexion
import six

from openapi_server.models.io_file import IOFile  # noqa: E501
from openapi_server.models.io_request import IORequest  # noqa: E501
from openapi_server.models.model import Model  # noqa: E501
from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server import util

import requests


def list_models_post():  # noqa: E501
    """Obtain a list of current models

    Request a list of currently available models. # noqa: E501


    :rtype: List[str]
    """
    params = (
        ('endpoint', 'https://endpoint.mint.isi.edu/ds/query'),
    )

    response = requests.get('https://query.mint.isi.edu/api/mintproject/MINT-ModelCatalogQueries/getModels', params=params)
    models_ = response.json()['results']['bindings']
    models = [m['label']['value'] for m in models_]

    return models


def model_config_model_name_get(ModelName):  # noqa: E501
    """Obtain an example model configuration.

    Submit a model name and receive a model configuration for the given model. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: ModelConfig
    """
    response = requests.get('https://query.mint.isi.edu/api/mintproject/MINT-ModelCatalogQueries/getModelConfigurations')
    configs = []
    for conf in response.json()['results']['bindings']:
        if ModelName.lower() in conf.get('desc',{}).get('value',{}).lower():
            configs.append(conf)
    return configs

def model_info_model_name_get(ModelName):  # noqa: E501
    """Get basic metadata information for a specified model.

    Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run. # noqa: E501

    :param model_name: The name of a model.
    :type model_name: str

    :rtype: Model
    """
    response = requests.get(f'https://api.models.mint.isi.edu/v0.0.2/model/{ModelName}')
    return response.json()


def model_io_post():  # noqa: E501
    """Obtain information on a given model&#39;s inputs or outputs.

    Submit a model name and receive information about the input or output files required by this model. # noqa: E501

    :param io_request: The name of a model and an IO type.
    :type io_request: dict | bytes

    :rtype: List[IOFile]
    """
    if connexion.request.is_json:
        io_request = IORequest.from_dict(connexion.request.get_json())  # noqa: E501
        name_ = io_request.name
        type_ = io_request.iotype
        params = (
            ('model', f"https://w3id.org/mint/instance/{name_}"),
            ('endpoint', 'https://endpoint.mint.isi.edu/ds/query'),
        )

        response = requests.get('https://query.mint.isi.edu/api/mintproject/MINT-ModelCatalogQueries/getVariablePresentationsForModel', params=params)
        var_rep = response.json()['results']['bindings'][0]
        input_files = var_rep['input_files']['value'].split(', ')
        output_files = var_rep['output_files']['value'].split(', ')
        if type_ == 'input':
            f_ = input_files
        else:
            f_ = output_files
        files_variables = []
        for f in f_:
            files_variables.append(util._get_variables(f))
        return files_variables
