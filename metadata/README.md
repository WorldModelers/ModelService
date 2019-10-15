# Setting up Concept Mapping

By running `maas_install.sh` (which directly calls `Concepts-to-Redis.py`) each `model-metadata.yaml` file will be read in.

This script ensures that there is a Redis key called `concepts` which is a set of all mapped concept names.

Each concept name is then made its own key, whose value is a set of model names associated with that concept.