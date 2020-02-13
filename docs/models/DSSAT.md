---
layout: default
parent: Models Overview
---

# DSSAT

DSSAT is executable through MaaS using a Docker container provided by UFL and an associated Docker data volume. However, this execution capability is limited to: 

- maize only
- Ethiopia only
- limited parameterization

For the January, 2020 experiment, UFL provided a set of model runs, in `.csv` format, each of which pertained to a discrete run. This added up to hundreds of `.csv` files. The file names contained parameterization information, which was parsed prior to ingesting the data into MaaS.

## Format

DSSAT data is provided in `.csv` format both by UFL (for standalone runs) and by the Docker container which executes the model.

## Resolution

DSSAT output is provided at the 10km resolution. DSST output is provided at the daily level. For a given set of parameters, DSSAT outputs harvest and planting date information, as well as the weight of the crop yielded per harvest day over the time range of interest. MaaS does not currently aggregate this to a temporally higher level (e.g. monthly)

## Processing

DSSAT has a dual path in MaaS: Docker execution and standalone run integration.

- **Docker Executution**: this is handled by the [`dssat.py` controller](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/dssat.py) in the MaaS REST Service. This calls the Docker container and submits the parameters selected by the user. The Docker container and data volume can be built using this [`maas_install.sh` script](https://github.com/WorldModelers/ModelService/blob/master/DSSAT-Integration/maas_install.sh). MaaS uses [`RQ`](https://python-rq.org/) for asynchronously managing Dockerized execution. So, once the Docker container has finished running, the `dssat.py` controller obtains the output, stores it to S3, puts the appropriate run metadata in Redis, and normalizes the output into the MaaS DB.
- **Standalone Runs**: There are separate scripts for processing each batch of standalone runs provided by UFL. These scripts operate on a per `crop` basis. For example, [`DSSAT_processing_sorghum.py`](https://github.com/WorldModelers/ModelService/blob/master/DSSAT-Integration/DSSAT_processing_sorghum.py) handles processing Sorghum DSSAT data. These sripts parse the file names for each UFL-provided `.csv` to determine that respective run's parameters. The data is then stored to S3, metadata stored to Redis, and the output is normalized and finally stored to PostGres.

## Issues/Lessons Learned

- It is difficult to manage and keep up-to-date a dual integration path for any model. 
- DSSAT is a moderately time consuming model to run (3-4 hours per run on an AWS server), so pre-caching thousands of runs would need to be accomplished in a distributed fashion.
- MaaS execution of DSSAT is hampered by having only limited geography and crop options.
