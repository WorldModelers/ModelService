---
layout: default
parent: Models Overview
---

# LPJmL Models

There are three LPJmL-based models currently integrated into MaaS:

- Yield Anomalies LPJmL
- LPJmL Historic
- LPJmL 2018

Currently none of these models are executable via MaaS. PIK provided pre-run outputs for each model. 

## Format

The _Yield Anomalies LPJmL_ data was provided as global `.GeoTIFF`s for 2018.

_LPJmL Historic_ was provided in the LPJmL model-specific binary format and required transformation into point-based data. An example Jupyter Notebook for performing this transformation [can be found here](https://github.com/WorldModelers/ModelService/blob/master/LPJmL-Integration/parse_crop_mask.ipynb). Additionally, this Notebook includes specifications for mapping LPJmL output to the [crop mask used by PIK](https://github.com/WorldModelers/ModelService/tree/master/LPJmL-Integration/data/landuse_patterns).

_LPJmL 2018_ was also provided in the LPJmL model-specific binary format and required the same transformations as did the _LPJmL Historic_ model data. 

## Resolution

Each LPJmL model is run at a 50km resolution. Output for the scenarios from _LPJmL_2018_ are daily production estimates within 2018. For _LPJmL Historic_ they are daily production estimates from 1984 onward. _Yield Anomalies LPJmL_ are annual for 2018. 

## Processing

Each run for _LPJmL_2018_ is mapped to a historic climate year. Information on each climate year [can be found here](https://docs.google.com/spreadsheets/d/1Oqhfdv0in68evpRga9oDjDFN26SuNb0A00awO1mSXTc/edit#gid=1615346066). This mapping enables the user to select a year with some specified precipitation/temperature levels and model 2018 given that specification.

_Yield Anomalies LPJmL_ relies on two processing scripts:

1. [`yield_anomalies_data.py`](https://github.com/WorldModelers/ModelService/blob/master/Yield-Anomalies-Integration/yield_anomalies_data.py) which stores the run metadata to Redis
2. [`yield_anomalies_processing.py`](https://github.com/WorldModelers/ModelService/blob/master/Yield-Anomalies-Integration/yield_anomalies_processing.py) which normalizes the output and stores it to the MaaS DB.

## Issues/Lessons Learned

- Running LPJmL is complex, but preparing its data inputs is even more challenging. This process needs to be documented by PIK in detail so that it can be adequately incorporated into SuperMaaS.
- Model-specific binary formats such as LPJmL's are a challenge becasue it is hard to automate the ingestion of these outputs without existing code for normalization. A standard such as NetCDF would be preferable.
- Errors in the data preparation can easily cause downstream problems with such complex models; since they take significant time to run this presents a challenge. It would be useful to know how "bad" the results are with faulty input data or a flawed input preparation process. If they are 95% wrong that is one thing, but if they are 5% wrong that is entirely different and may be acceptable to some users.