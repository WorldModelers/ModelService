---
layout: default
parent: Models Overview
---

# TWiST

TWiST is an executable model integrated into MaaS. The executable/MaaS branch for TWiST [can be found here](https://github.com/cstotto/multi_twist/tree/production_shock_docker_version). From this, a Docker container is built on the MaaS server and managed with the [TWiST controller](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/twist.py).

TWiST was pre-run (through MaaS) to produce outputs for the January Experiment. 

TWiST currently only provides wheat prices.

## Format

TWiST outputs are in `.csv` format.

## Resolution

TWiST produces global monthly prices. 

## Processing

All processing is handled by the [TWiST controller](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/twist.py). This executes the TWiST Docekr container based on the user's parameterization, normalizes the model output, stores the output to S3 and to the MaaS DB, and stores the run metadata to Redis.

## Issues/Lessons Learned

- This model is a lightweight Python-based model whose pre-run outputs provided by PIK align with the Docker container's output. This means that it can be readily and tightly integrated into MaaS, as it is.
- The primary limitation of this model is that it only provides wheat prices and does not have information about other crops.

