# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.models.run_results import RunResults  # noqa: E501
from openapi_server.models.run_status import RunStatus  # noqa: E501
from openapi_server.test import BaseTestCase


class TestExecutionController(BaseTestCase):
    """ExecutionController integration test stubs"""

    def test_available_results_get(self):
        """Test case for available_results_get

        Obtain a list of run results
        """
        query_string = [('model_name', 'model_name_example'),
                        ('size', 56)]
        response = self.client.open(
            '/available_results',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_runs_model_name_get(self):
        """Test case for list_runs_model_name_get

        Obtain a list of runs for a given model
        """
        response = self.client.open(
            '/list_runs/{ModelName}'.format(model_name='model_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_result_file_result_file_name_get(self):
        """Test case for result_file_result_file_name_get

        Obtain the result file for a given model run.
        """
        response = self.client.open(
            '/result_file/{ResultFileName}'.format(result_file_name='result_file_name_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_run_model_post(self):
        """Test case for run_model_post

        Run a model for a given a configuration
        """
        model_config = ModelConfig()
        response = self.client.open(
            '/run_model',
            method='POST',
            data=json.dumps(model_config),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_run_results_run_idget(self):
        """Test case for run_results_run_idget

        Obtain metadata about the results of a given model run
        """
        response = self.client.open(
            '/run_results/{RunID}'.format(run_id='run_id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_run_status_run_idget(self):
        """Test case for run_status_run_idget

        Obtain status for a given model run
        """
        response = self.client.open(
            '/run_status/{RunID}'.format(run_id='run_id_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
