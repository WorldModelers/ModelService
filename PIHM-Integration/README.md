# PIHM Integration

This directory contains a script called `pihm_processing.py` which takes in a PIHM metadata CSV file which should be named `pihm-v4.1.0_{region}.csv` where `{region}` is the name of the region for the set of PIHM runs (e.g. Baro). The PIHM metadata file contains information on the two primary parameters for PIHM:

* precipitation
* temperature

The metadata file also contains information on the start/end for each run as well as the URL for obtaining the result files.

`pihm_processing.py` iterates through each metadata CSV and downloads the results. It then adds the run to Redis and uploads the raw `.tif` file (called `Flood_surf.tif`) to S3. It then reprojects this file, normalizes it, and pushes the resulting data to the MaaS database.