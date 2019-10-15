# Setting up Concept Mapping

By running `maas_install.sh` you invoke two scripts:

### `Concepts-to-Redis.py` 

This ensures that there is a Redis key called `concepts` which is a set of all mapped concept names per each `**model-metadata.yaml` file.

Each concept name is then made its own key, whose value is a set of model names associated with that concept.

### `Metadata-to-Redis.py`. 

This reads in each `**model-metadata.yaml` file and ensures that the model metadata is stored in Redis based on the model `id`. For example, DSSAT has a key in Redis called `DSSAT-meta` whose value is a JSON dump of the YAML metadata file.

