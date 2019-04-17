# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.model_config import ModelConfig  # noqa: E501
from openapi_server.test import BaseTestCase


class TestExecutionController(BaseTestCase):
    """ExecutionController integration test stubs"""

    def test_validate_config_post(self):
        """Test case for validate_config_post

        Submit a model configuration for validation
        """
        model_config = ModelConfig()
        response = self.client.open(
            '/validate_config',
            method='POST',
            data=json.dumps(model_config),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
