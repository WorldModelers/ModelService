#!/usr/bin/env python
# coding: utf-8

import glob
import redis
import configparser
from hashlib import sha256
import json
import yaml
from pprint import pprint


metadata_files = []
for filename in glob.iglob('**model-metadata.yaml', recursive=True):
     metadata_files.append(filename)

print(*metadata_files, sep = "\n")

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])


if __name__ == "__main__":
    models = []

    for m in metadata_files:
        with open(m, 'r') as stream:
            model = yaml.safe_load(stream)
            models.append(model)

    for m in models:
        r.set(f"{m['id']}-meta", json.dumps(m))

    print("We can obtain the metadata associated with the population model for example...\n")
    pprint(json.loads(r.get('population_model-meta').decode('utf-8')))            