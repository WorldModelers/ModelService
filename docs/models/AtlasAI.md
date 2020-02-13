---
layout: default
parent: Models Overview
---

# Atlas AI Models

The Atlas AI models include:

* Asset Wealth Model
* Consumption Model
* Cropland Use Model

These models are based on proprietary algorithms developed by Atlas AI. Therefore, it is **not likely** that MaaS will ever include executable versions of these models. 

## Format

Each model output was provided as a multi-band raster (`.GeoTIFF`) via a secure Google Cloud Platform. Each band represents a range of years which was specified in a set of README files that was provided by Atlas. The _Cropland Use Model_ was provided as a mosaic of rasters which had to be combined. 

## Resolution

The _Asset Wealth_ and _Consumption Model_ were provided at a 2km resolution. The _Cropland Use Model_ was provided at varying resolutions down to 120m resolution. This fine grained resolution proved too unwieldy to work with in the short-term, so only the 480m resolution data was ingested into MaaS. 

## Protecting Atlas AI data

Atlas AI data is the only data available through MaaS that is not public. Atlas requested that downloads of its datasets be protected by HTTP basic auth. So, Atlas AI datasets are not available through S3 directly. Instead, they are stored to the MaaS server filesystem and served via HTTP basic auth. They are the only models for which the [`result_file`](https://worldmodelers.com/ModelService/api_docs/ExecutionApi.html#result_file_result_file_name_get) endpoint is at all relevant.

## Processing

The Atlas models are normalized and ingested into MaaS through a couple scripts:

- [`atlas_data.py`](https://github.com/WorldModelers/ModelService/blob/master/Atlas-Integration/atlas_data.py) pushes the Atlas AI outputs to S3, generates appropriate keys in Redis, and stores them to the MaaS filesystem.
- [`atlas_processing.py`](https://github.com/WorldModelers/ModelService/blob/master/Atlas-Integration/atlas_processing.py) converts the `.GeoTiff` files into point-based tabular data and stores it in PostGres
- [`cropland_processing.py`](https://github.com/WorldModelers/ModelService/blob/master/Atlas-Integration/Cropland_processing.py) does the process the prior two scripts provide except for the _Cropland Use Model_, which was a later addition to MaaS.

## Issues/Lessons Learned

- Atlas AI data could be provided in a _more_ normalized format, with consistent time ranges per band for each model and a consistent resolution (e.g. 1km)
- It is awkward to have an endpoint just designed for these proprietary models ([`result_file`](https://worldmodelers.com/ModelService/api_docs/ExecutionApi.html#result_file_result_file_name_get)) and the solution for that endpoint is somewhat hacky.
