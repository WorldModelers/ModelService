#!/usr/bin/env python
# coding: utf-8

import glob
import redis
import configparser
from hashlib import sha256
import json
import yaml
from pprint import pprint
import os
import requests

metadata_files = []
for filename in glob.iglob('../metadata/models/**model-metadata.yaml', recursive=True):
     metadata_files.append(filename)

print(*metadata_files, sep = "\n")

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

host = config['UAZ-CONCEPTS']['HOST']
port = config['UAZ-CONCEPTS']['PORT']
endpoint = config['UAZ-CONCEPTS']['ENDPOINT']
concept_mapper_endpoint = f"http://{host}:{port}/{endpoint}"

headers = {
    'Content-Type': 'application/json',
}

def main():
    ##########################################
    ########### Setting up concepts ##########
    ##########################################
    print("Setting up concepts...")
    models = {}

    for m in metadata_files:
        with open(m, 'r') as stream:
            model = yaml.safe_load(stream)
            models[model['id']] = model

    concepts_m = {}
    concepts_p = {}
    concepts_o = {}

    # for each model
    for kk, vv in models.items():
        
        # use UAZ concept mapping service to get model level concepts
        data = {"name": kk, "examples": [vv['description'], vv['label']]}
        response = requests.post(concept_mapper_endpoint, headers=headers, json=data)
        model_concepts = response.json()['conceptMatches']

        # get its concepts
        for concept in model_concepts:
            cc = concept['concept']
            m_ = {'name': kk, 'score': concept['score'], 'type': 'model'}
            # if concept not in concepts dict, add it
            if cc not in concepts_m:
                concepts_m[cc] = set()
                concepts_m[cc].add(json.dumps(m_))

            # if concept in concepts, add model to set
            else:
                concepts_m[cc].add(json.dumps(m_))    

        # get its parameters
        for pp in vv.get('parameters',[]):

            # use UAZ mapping service to map concepts
            data = {"name": pp["name"], "examples": [pp["name"], pp["description"]]}
            response = requests.post(concept_mapper_endpoint, headers=headers, json=data)
            cons = response.json()['conceptMatches']

            # if concept not in concepts dict, add it
            for concept in cons:
                cc = concept['concept']
                pp['model'] = kk
                pp['type'] = 'parameter'
                pp['score'] = concept['score']
                if cc not in concepts_p:
                    concepts_p[cc] = set()
                    concepts_p[cc].add(json.dumps(pp))

                # if concept in concepts, add model to set
                else:
                    concepts_p[cc].add(json.dumps(pp))
                    
        # get its variables
        for oo in vv.get('outputs',[]):

            # use UAZ mapping service to map concepts
            data = {"name": oo["name"], "examples": [oo["name"], oo["description"]]}
            response = requests.post(concept_mapper_endpoint, headers=headers, json=data)
            cons = response.json()['conceptMatches']

            # if concept not in concepts dict, add it    
            for concept in cons:
                cc = concept['concept']
                oo['model'] = kk
                oo['type'] = 'output'                
                oo['score'] = concept['score']
                if cc not in concepts_o:
                    concepts_o[cc] = set()
                    concepts_o[cc].add(json.dumps(oo))
                # if concept in concepts, add model to set
                else:
                    concepts_o[cc].add(json.dumps(oo))    

    concept_names = set(list(concepts_m.keys()) + list(concepts_o.keys()) + list(concepts_p.keys()))

    # delete the "concepts" set 
    # ensures clean start based on model-metadata files
    r.delete('concepts')

    # add concepts to "concepts" set in Redis
    for c in concept_names:
        r.sadd('concepts', c)

    combined = {'model': concepts_m,
                'parameter': concepts_p,
                'output': concepts_o
                }

    # if key for concept exists, delete it 
    # this ensures a fresh start from whatever is in the model metadata file
    for cc in concept_names:
        if r.exists(cc):
            r.delete(cc)
            
    for tt, cons in combined.items():
        
        for cc, vv in cons.items():

            # for each item associated with each concept
            for ee in vv:
                # add the model to a Redis set named for the concept name
                r.lpush(cc, ee)
                                
    ##########################################
    ########### Setting up metadata ##########
    ##########################################
    print("Setting up metadata...")
    models = []
    for m in metadata_files:
            with open(m, 'r') as stream:
                model = yaml.safe_load(stream)
                models.append(model)

    if r.exists('model-list'):
        print("Deleting model-list set...")
        r.delete('model-list')
    else:
        pass

    for m in models:
        r.set(f"{m['id']}-meta", json.dumps(m))
        r.sadd('model-list',m['id'])            

if __name__ == "__main__":
    main()

    print("We can obtain the models associated with 'economy', for example:")
    elements = [json.loads(i.decode('utf-8')) for i in r.lrange( "rainfall", 0, -1 )]
    pprint(elements)