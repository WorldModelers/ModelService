---
layout: default
parent: Models Overview
---

# AgMIP’s Seasonal Crop Yield Emulator

This emulator provided by Columbia features a set of static pre-run outputs. This is not executable through MaaS. It provides yield anomaly inforamtion for maize and spring wheat.


## Format

This emulator's outputs are all `.csv` files. The pre-run outputs are [available here](https://github.com/WorldModelers/ModelService/tree/master/AGMIP-Integration/data). Each output file's `path` contains information about the parameters used for each of the emulator runs. 

## Resolution

The point resolution of the AgMIP emulator is unclear. It covers only 2018. 

## Processing

This emulator was not fully integrated into MaaS due to time constraints. The outputs were formatted and visualized in Tableau for the January Experiment, but the data was never stored in the MaaS database. The [raw data](https://github.com/WorldModelers/ModelService/tree/master/AGMIP-Integration/data) is processed into a [normalized format](https://github.com/WorldModelers/ModelService/tree/master/AGMIP-Integration/data_processed) by the [`AGMIP_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/AGMIP-Integration/AGMIP_processing.py). This script performs normalization only, and does not ingest the output into the MaaS DB or store metadata to Redis.

## Issues/Lessons Learned

- This AgMIP emulator output is lightweight and suggests that the model itself may be lightweight as well, however Jataware has had no visibility to the model code.