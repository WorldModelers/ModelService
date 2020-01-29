# Model Documentation

This directory contains information related to capturing structured metadata about each bottom-up model on World Modelers.

### Key Metadata Concepts

There are 4 primary concepts to consider with respect to capturing metadata about models:

* `Outputs`: these are the output variables produced by the model. They are generally predictions.
* `Parameters`: these are the "tunable knobs" which may be adjusted by a user prior to running a model. For example, the user may select a geographic area, time interval, or perturb something about the model's initialization.
* `configuration`: This defines an example configuration for the model (e.g. the defaults).

## The Example Model

To facilitate capturing this information for each model, we use a standardized [YAML](https://yaml.org/) file. YAML is preferred to JSON since it allows for in-line comments, can be easily version controlled, but is also serializable to JSON. 

> Note that if keys are missing in the YAML file, **MaaS will not start**.

### Outputs

The [example-model.yaml](../metadata/example-model.yaml) file contains an example for a toy flood model. This model has one `output`. The `example-model.yaml` contains examples of how this metadata should be defined.

### Parameters

Parameters are user "tunable knobs". The goal is to loosely define these parameters in a way where their general type is known and we have minimal descriptions of each parameter. However, these parameters will not be type checked. So, for example, a `TimeParameter` is really a string provided in the format expected by the model. There are 4 types of parameters:

1. `NumberParameter`: this can be either an integer or float (whichever is expected by the model)
2. `StringParameter`: this is a parameter type for any string
3. `ChoiceParameter`: this should be a user choice from a constrained list
4. `TimeParameter`: this is a time related parameter provided as a string in the format expected by the model
5. `GeoParameter`: this is a geospatial parameter in the format expected by the model (e.g. GeoJSON)

> Note: default values **must** be provided for each parameter.

## Loading YAML

You can load and parse the model YAML using the [Python pyyaml library](https://pyyaml.org/wiki/PyYAMLDocumentation). For example:

```
import yaml
with open("example-model.yaml", 'r') as stream:
    model = yaml.safe_load(stream)

print(model['input_files'][0]['variables'][0])
```

prints the first variable from the first input file.

## Schema validation

You can validate all the YAML schemas by running `validate.py` from the `metadata` directory. This relies on the `metadata-schema.json` file which is also stored in that same directory.

## Conveting YAML to human readable `.docx`

You can convert the YAML files to a (more) human readable `.docx` form using the `metadata-to-docx.py` script in the `metadata` directory. You can run this with `python metadata-to-docx.py`.