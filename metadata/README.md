# Setting up Concept Mapping

By running `maas_install.sh` you invoke `Concepts-to-Redis.py` and `Metadata-to-Redis.py`. This reads in each `model-metadata.yaml` file and ensures that the model metadata is stored in Redis.

This also ensures that there is a Redis key called `concepts` which is a set of all mapped concept names.

Each concept name is then made its own key, whose value is a set of model names associated with that concept.