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

metadata_files = []
for filename in glob.iglob('../metadata/models/**model-metadata.yaml', recursive=True):
     metadata_files.append(filename)

print(*metadata_files, sep = "\n")

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

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

    concepts = {}

    # for each model
    for kk, vv in models.items():
        
        # get its concepts
        for cc in vv.get('concepts',[]):
            
            # if concept not in concepts dict, add it
            if cc not in concepts:
                concepts[cc] = set()
                concepts[cc].add(kk)
                
            # if concept in concepts, add model to set
            else:
                concepts[cc].add(kk)


    print("Concept mapping to models:")
    pprint(concepts)


    concept_names = set(concepts.keys())

    # delete the "concepts" set 
    # ensures clean start based on model-metadata files
    r.delete('concepts')

    # add concepts to "concepts" set in Redis
    for c in concept_names:
        r.sadd('concepts', c)

    print("We can obtain all concepts:")
    pprint(r.smembers('concepts'))

    #for each concept
    for cc, vv in concepts.items():
        
        # if key for concept exists, delete it 
        # this ensures a fresh start from whatever is in the model metadata file
        if r.exists(cc):
            r.delete(cc)
        
        # for each model associated with each concept
        for ee in vv:
            
            # add the model to a Redis set named for the concept name
            r.sadd(cc, ee)

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
        print("Deleteing model-list set...")
        r.delete('model-list')
    else:
        pass

    for m in models:
        r.set(f"{m['id']}-meta", json.dumps(m))
        r.sadd('model-list',m['id'])            

if __name__ == "__main__":
    main()

    print("We can obtain the models associated with 'economy', for example:")
    pprint(r.smembers('economy'))