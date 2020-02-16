---
layout: default
parent: Models Overview
---

# External Models

There is currently only one external model: _World Pop_.

> In this context, an external model is _external to the World Modelers program_

## Format

_World Pop_ outputs are provided in [`GeoTIFF` format](https://www.worldpop.org/geodata/summary?id=124).

## Resolution

_World Pop_ is provided in annual estimates (one estimate every five years) at the 100m level.

## Processing

There are two scripts used for processing _World Pop_ data:

1. `[world_population_data.py`](https://github.com/WorldModelers/ModelService/blob/master/World-Population-Integration/world_population_data.py) adds run metadata to Redis and pushes the raw model output to S3
2. [`world_population_processing.py`](https://github.com/WorldModelers/ModelService/blob/master/World-Population-Integration/world_population_processing.py) normalizes the model output and stores it to the MaaS DB.

## Issues/Lessons Learned

- Since _World Pop_ is well documented, it was quite easy to integrate its static runs into MaaS. 
- It would be relatively simple to add additional, well-documented, external models to MaaS. The primary challenge would be in automatically updating these models in MaaS when new model results are published.