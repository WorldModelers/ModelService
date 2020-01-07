from jsonschema import validate
import yaml
import json
import os

with open("metadata-schema.json","r") as f:
    schema = json.loads(f.read())

models = os.listdir('models')

for m in models:
    print(f"Validating schema for {m}")

    with open(f'models/{m}', 'r') as stream:
        model = yaml.safe_load(stream)

    validate(instance=model, schema=schema)