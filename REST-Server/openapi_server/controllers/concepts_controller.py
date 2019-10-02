import connexion
import six

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server import util

import configparser
import redis

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

def concept_mapping_concept_get(Concept):  # noqa: E501
    """Get an array of models related to a concept.

    Submit a concept name and receive an array of model related to that concept. # noqa: E501

    :param concept: The name of a concept.
    :type concept: str

    :rtype: Concept
    """
    models = [m.decode('utf-8') for m in list(r.smembers(Concept))]
    return models


def list_concepts_get():  # noqa: E501
    """Obtain a list of available concepts

    Request a list of currently available concepts. These are derived from the list of  [UN indicators](https://github.com/WorldModelers/Ontologies/blob/master/performer_ontologies/un_to_indicators.tsv) and are tied to model output variables.  # noqa: E501


    :rtype: List[str]
    """
    concepts = [c.decode('utf-8') for c in list(r.smembers('concepts'))]
    return concepts
