# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server.test import BaseTestCase


class TestConceptsController(BaseTestCase):
    """ConceptsController integration test stubs"""

    def test_concept_mapping_get(self):
        """Test case for concept_mapping_get

        Obtain an array of models related to a concept.
        """
        query_string = [('concept', 'wm/concept/causal_factor/agriculture/planting'),
                        ('concept_type', 'output')]


        print(f"Sending concept {query_string[0][1]} with concept_type {query_string[0][1]}")
        response = self.client.open(
            '/concept_mapping',
            method='GET',
            query_string=query_string)

        resp = json.loads(response.data.decode('utf-8'))
        print(f"Found {len(resp)} outputs from /concept_mapping")
        
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_list_concepts_get(self):
        """Test case for list_concepts_get

        Obtain a list of available concepts
        """
        response = self.client.open(
            '/list_concepts',
            method='GET')

        resp = json.loads(response.data.decode('utf-8'))
        print(f"Found {len(resp)} concepts.")

        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
