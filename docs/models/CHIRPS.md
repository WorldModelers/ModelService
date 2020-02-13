---
layout: default
parent: Models Overview
---

# CHIRPS

CHIRPS has two associated models integrated into MaaS:

* CHIRPS
* CHIRPS-GEFS

These models are provied as a data service by UCSB. They are "executable" in MaaS in so far as a new set of parameters can be provided to the [`/run_model`](https://worldmodelers.com/ModelService/api_docs/ExecutionApi.html#run_model_post) endpoint and the corresponding data, if not in MaaS already, will be fetched from UCSB, normalized, and pulled into the MaaS DB. To accomplish this, MaaS relies on UCSB's REST service.

## Format

After MaaS makes an API call to the _CHIRPS_ (or _CHIRPS-GEFS_) service, UCSB sends back (synchronously) a `.GeoTIFF` based on the specified parameters. 

## Resolution

These models are provided at the 5km resolution. _CHIRPS_ is provided as 10-day (dekadal) historic data. _CHIRPS-GEFS_ is provided as a 10-day (dekadal) forward looking forecast. Currently, MaaS does not collapse these model outputs into higher-level (e.g. monthly) outputs.

## Processing

_CHIRPS_ and _CHIRPS-GEFS_ are normalized and ingested into MaaS through the [`chirps.py` controller](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/chirps.py) in the MaaS REST Service.

This does a few things:

- converts the user's `/run_model` request into a format that can be interpreted by UCSB's data service. This includes reprojecting the `bbox` (geo bounding box) parameter provided by the user from `WGS84  coordinate system` to `Web Mercator`.
- obtains results from UCSB in `.GeoTIFF` and converts it to point based vector data
- stores the raw data to S3, the normalized data to PostGres, and stores the run information to Redis

## Issues/Lessons Learned

- The time resolution is a major issue for Uncharted. These models have time (`year` and `dekad`) as parameters for their runs. Uncharted would prefer that time parameters are abstracted for them, so that each model run is a _whole time series_, instead of each run being _part of a time series_
- MaaS is reliant on UCSB's data service. During the lead-up to the January, 2020 experiment the data service URI changed and the MaaS integration (briefly) broke
