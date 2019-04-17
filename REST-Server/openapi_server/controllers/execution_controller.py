import connexion
import six

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server import util


def validate_config_post(model_config):  # noqa: E501
    """Submit a model configuration for validation

    Submit a model configuration for a given model to determine if the configuration meets the model&#39;s requirements. # noqa: E501

    :param model_config: A model configuration.
    :type model_config: dict | bytes

    :rtype: ModelConfig
    """
    if connexion.request.is_json:
        model_config = ModelConfig.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
