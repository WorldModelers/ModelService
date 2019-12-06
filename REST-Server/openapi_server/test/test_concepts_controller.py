# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server.models.concept_request import ConceptRequest  # noqa: E501
from openapi_server.test import BaseTestCase


class TestConceptsController(BaseTestCase):
    """ConceptsController integration test stubs"""

    def test_concept_mapping_post(self):
        """Test case for concept_mapping_post

        Obtain an array of models related to a concept.
        """
        concept_request = ConceptRequest()
        response = self.client.open(
            '/concept_mapping',
            method='POST',
            data=json.dumps(concept_request),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_concepts_get(self):
        """Test case for list_concepts_get

        Obtain a list of available concepts
        """
        response = self.client.open(
            '/list_concepts',
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
