---
layout: default
parent: Models Overview
---

# PIHM

The Penn State Integrated Hydrologic Modeling System (PIHM) model is produced by the MINT team and is not executable through MaaS. It was provided with MINT metadata which describes the run parameters and the location from which to download the data. [Here are the MINT metadata files](https://github.com/WorldModelers/ModelService/tree/master/PIHM-Integration/PIHM-Meta-Files). Each basin covered by the standalone runs is provided in separate `.csv` metadata file.

We are able to run PIHM through it's Docker container with the following command:

```bash
docker run --rm -v $PWD:/mint -it mintproject/pihm:v2 bash
```

However, we are not clear how to parameterize the run, so the output of the Docker command will be for one fixed run with unknown parameters.

## Format

PIHM model output is multi-band `.GeoTIFF`. Each band represents a month. Each

## Resolution

PIHM output is at 200m resolution. It is monthly. The geospatial resolution is not collapsed by MaaS to something more coarse-grained (e.g. 1km).

## Processing

Since PIHM is provided as standalone runs, the [`pihm_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/PIHM-Integration/pihm_processing.py) downloads each file listed in the [MINT metadata files](https://github.com/WorldModelers/ModelService/tree/master/PIHM-Integration/PIHM-Meta-Files), stores it to S3 and captures metadata to Redis for each run. It then takes these downloaded files, converts them from `.GeoTIFF` to point based data and stores them to PostGres. 

## Issues/Lessons Learned

- Since PIHM appears to have a working Docker container, we seem reasoably close to be able to execute it via MaaS. Execution of the container takes approximately 24 hours.
- 200m resolution is too fine grained for MaaS and caused database bloat without providing significant value
- This model was specifically requested during the January, 2020 experiment to have additional tunable parameters exposed. Currently only evapotranspiration and temperature are exposed.
