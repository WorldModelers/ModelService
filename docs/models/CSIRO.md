---
layout: default
parent: Models Overview
---

# CSIRO Models

There are three CSIRO models currently integrated into MaaS:

- APSIM
- G-Range
- CLEM

Currently none of these models are executable via MaaS. CSIRO provided pre-run outputs for each model. Each run maps to a _scenario_. Each _scenario_ corresponds to a set of run parameters. The [_scenario_ definitions can be found here](https://github.com/WorldModelers/ModelService/blob/master/CSIRO-Integration/Scenarios.csv).

## Format

All CSIRO model output was provided as `.csv` files. Each `.csv` contained multiple features, and in the case of _APSIM_ and _G-Range_, multiple crops as well. 

## Resolution

Each CSIRO model uses the same gridcell system, which provides outputs at the 25km resolution. The gridcell mapping (cell to lat/lon) is [available here](https://github.com/WorldModelers/ModelService/blob/master/CSIRO-Integration/Experiment%202020-01%20-%20Gridcell%20Centre%20Points.csv). For each model, CSIRO provided long-term historic averages as well as 2018 annual estimates. 

## Processing

Each CSIRO model has a separate processing script that normalizes its output, stores its run metadata to Redis and raw output to S3, and stores the normalized outputs to the MaaS DB:

- [`APSIM_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/CSIRO-Integration/APSIM_processing.py)
- [`G-Range_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/CSIRO-Integration/G-Range_processing.py)
- [`CLEM_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/CSIRO-Integration/CLEM_processing.py)

These scripts handle the issues associated with separating long-term historical runs from 2018 scenario-based runs.

## Issues/Lessons Learned

- Models like CSIRO's which have many features end up bloating the MaaS database given the current structure. Since each feature requires its own row, a 10 feature x 100 record `.CSV` would end up having 1000 DB records in the MaaS DB. 
- Similarly models with large parameter spaces such as CSIRO's end up with many runs (made explicit in the DB) which were implicit in the model output. For example, each crop is treated as a separate run in MaaS, while in _APSIM_ and _G-Range_ they are just features of a given scenario.
- Modelers need to improve what they consider to be a parameter. CSIRO scenarios include parameters like "cereal production percentile ranking" which is really just a comparison of the model outputs for a given scenario with outputs from other scenarios. Including this parameter caused confusion among modelers at the January Experiment.