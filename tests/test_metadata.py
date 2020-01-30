from jsonschema import validate
import yaml
import json
import glob

with open("metadata/metadata-schema.json","r") as f:
    schema = json.loads(f.read())

models = glob.glob("metadata/models/*.yaml")

for m in models:
    print(f"Validating schema for {m.split('/')[-1]}")

    with open(f"{m}", "r") as stream:
        model = yaml.safe_load(stream)
    
    valid = validate(instance=model, schema=schema)
    assert valid == None