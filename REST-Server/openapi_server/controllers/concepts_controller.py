import connexion
import six

from openapi_server.models.concept import Concept  # noqa: E501
from openapi_server import util

import configparser
import redis
import json

config = configparser.ConfigParser()
config.read('config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

def concept_mapping_get(concept=None, concept_type=None):  # noqa: E501
    """Obtain an array of models related to a concept.

    Submit a concept name and optional type and receive an array of concepts related to that concept.        # noqa: E501

    :param concept: A concept name
    :type concept: str
    :param concept_type: The type of concept objects to return
    :type concept_type: str

    :rtype: List[Concept]
    """
    e = [json.loads(i.decode('utf-8')) for i in r.lrange(concept, 0, -1 )]
    if concept_type:
        e = [i for i in e if i['type']==concept_type]
    e = sorted(e, key=lambda k: k['score'], reverse=True) 
    return e


def list_concepts_get():  # noqa: E501
    """Obtain a list of available concepts

    Request a list of currently available concepts. These are derived from the list of  [UN indicators](https://github.com/WorldModelers/Ontologies/blob/master/performer_ontologies/un_to_indicators.tsv) and are tied to model output variables.  # noqa: E501


    :rtype: List[str]
    """
    concepts = [c.decode('utf-8') for c in list(r.smembers('concepts'))]
    return sorted(concepts)