# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.error import Error  # noqa: E501
from openapi_server.models.model import Model  # noqa: E501
from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.parameter import Parameter  # noqa: E501
from openapi_server.models.unknownbasetype import UNKNOWN_BASE_TYPE  # noqa: E501
from openapi_server.models.variable import Variable  # noqa: E501
from openapi_server.test import BaseTestCase


class TestExplorationController(BaseTestCase):
    """ExplorationController integration test stubs"""

    def test_list_models_post(self):
        """Test case for list_models_post

        Obtain a list of current models
        """
        response = self.client.open(
            '/list_models',
            method='POST')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_model_config_model_name_get(self):
        """Test case for model_config_model_name_get

        Obtain configurations for a given model.
        """
        response = self.client.open(
            '/model_config/{ModelName}'.format(model_name='model_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_model_info_model_name_get(self):
        """Test case for model_info_model_name_get

        Get basic metadata information for a specified model.
        """
        response = self.client.open(
            '/model_info/{ModelName}'.format(model_name='model_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_model_outputs_model_name_get(self):
        """Test case for model_outputs_model_name_get

        Obtain information on a given model's outputs.
        """
        response = self.client.open(
            '/model_outputs/{ModelName}'.format(model_name='model_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_model_parameters_model_name_get(self):
        """Test case for model_parameters_model_name_get

        Obtain information about a model's parameters.
        """
        response = self.client.open(
            '/model_parameters/{ModelName}'.format(model_name='model_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_search_post(self):
        """Test case for search_post

        Search for a model, dataset, or variable
        """
        unknown_base_type = UNKNOWN_BASE_TYPE()
        response = self.client.open(
            '/search',
            method='POST',
            data=json.dumps(unknown_base_type),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
