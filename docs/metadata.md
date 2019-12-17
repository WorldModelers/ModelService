# Model Documentation

This directory contains information related to capturing structured metadata about each bottom-up model on World Modelers. This information is critical for registering models to MINT.

### Key MINT Metadata Concepts

There are 4 primary concepts to consider with respect to capturing metadata about models:

1. `Inputs`: these are input files or datasets that are used by the model. They may change with some periodicity, but the underlying file structure remains the same (such as a daily weather file).
2. `Outputs`: these are the output files produced by the model. They are generally predictions.
3. `Parameters`: these are the "tunable knobs" which may be adjusted by a user prior to running a model. For example, the user may select a geographic area, time interval, or perturb something about the model's initialization.
4. `Variables`: these are fields in either `input` or `output` files.

## The Example Model

To facilitate capturing this information for each model, we use a standardized [YAML](https://yaml.org/) file. YAML is preferred to JSON since it allows for in-line comments, can be easily version controlled, but is also serializable to JSON to facilitate MINT registration. 

### Inputs and outputs

The [example-model.yaml](https://github.com/WorldModelers/ModelService/blob/master/Model-Docs/example-model.yaml) file contains an example for a toy flood model. This model has 1 `input` and 1 `output`. `Inputs` and `outputs` may be defined with optional metadata such as `spatial_coverage` or `temporal_coverage`. This facilitates geo/temporal search for models. The `example-model.yaml` contains examples of how this metadata should be defined.

### Variable definitions

`Variables` are tied directly to their corresponding `input` or `output`. Each `variable` should have a `standard_variable` from _an_ ontology (the modeler should choose the appropriate ontology).  A `variable` may have arbitrary metadata attached to it, such as `units`. 

### Examples
For `inputs`, you must specify one or more example files. These are actual instances of the `input` described. The example may have geospatial or temporal coverage. In the `example-model.yaml`, the `input` is a rainfall file, and the examples are actual instances of this rainfall file which vary by geogrpahy/time.

`outputs` do not need to have example files as these are generated directly by the model when the model is executed.

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