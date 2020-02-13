---
layout: default
parent: Models Overview
---

# Kimetrica Models

There are three Kimetrica models currently integrated into MaaS:

- Malnutrition Model
- Population Model
- Market Price Model

The _malnutrition model_ and _population models_ are **executable** through MaaS, while the _Market Price Model_ was integrated using standalone model output runs provided by Kimetrica. Theoretically, all Kimetrica models should be executable via MaaS since they all have a relatively consistent execution interface: [Luigi](https://luigi.readthedocs.io/en/stable/). 

## Format

All Kimetrica models are output as `.GeoTIFF` rasters. Since time is a parameter for these models, they are single band rasters, with the exception of the _Market Price Model_. The _Market Price Model_ has different commodities per raster band.

## Resolution

Each model is output at a 1km resolution. However, the _Market Price Model_ has constant data per Ethiopian region, so is actually regional-level data provided with 1k interpolation for the raster. The _Malnutrition_ and _Market Price Models_ have monthly output, the _Population Model_ has annual output.

## Processing

Since Kimetrica models are currently dual tracked with MaaS integration there are separate pathways for integrating the executable vs. the standalone models.

- **Docker Execution**: this is handled by the [`kimetrica.py` controller](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/kimetrica.py) in the MaaS REST Service. This calls the Kimetrica Docker container and submits the parameters selected by the user. The specific Luigi task sent to the container depends on the model which is being run. The logic for managing executing specific models within the same Kimetrica Docker container [is contained here](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/kimetrica.py#L42-L65). The Kimetrica Docker container can be built using this [`maas_install.sh` script](https://github.com/WorldModelers/ModelService/blob/master/Kimetrica-Integration/maas_install.sh). MaaS uses [`RQ`](https://python-rq.org/) for asynchronously managing Dockerized execution. So, once the Docker container has finished running, the `kimetrica.py` controller obtains the output, stores it to S3, puts the appropriate run metadata in Redis, and normalizes the output into the MaaS DB.
- **Standalone Runs**: for the _Market Price Model_, the standalone runs provided by Kimetrica are processed using the [`Market_price_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/Kimetrica-Integration/Market_price_processing.py). This handles data normalization, metadata storage, and S3/PostGres storage.

## Issues/Lessons Learned

- We are working with Kimetrica to streamline their model execution process. Since Luigi provides a common interface for executing Kimetrica models, it should be possible to machine read metadata provided about each model to automate its execution. This would reduce model specific logic contained in the `kimetrica.py` controller module.
- Models such as the _Market Price Model_ should likely be stored as GeoJSON, not as exploded point data. The process of taking regional level rasters and converting it to 1km point data bloats the MaaS DB. However, we need to coordinate with Uncharted to determine the best approach for handling varying data formats.
