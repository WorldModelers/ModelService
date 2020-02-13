---
layout: default
parent: Models Overview
title: Flood Severity Index
---

# FLood Severity Index Model

The Flood Severity Index (FSI) model is produced by the MINT team and is not executable through MaaS. It was provided with MINT metadata which describes the run parameters and the location from which to download the data. [Here is the MINT metadata file](https://github.com/WorldModelers/ModelService/blob/master/Flood-Index-Integration/Flood-Files.csv).

## Format

The FSI model output is `NetCDF`. It was provided in a well-formed and self-described `NetCDF` format which was relatively easy to understand.

## Resolution

This model's output is at 10km resolution. It provided daily information on severe, high and medium flood levels for each grid-cell. MaaS rolls this daily information up to the monthly level ([with this code](https://github.com/WorldModelers/ModelService/blob/master/Flood-Index-Integration/flood_index_processing.py#L109-L117)). This produces counts of days per month with severe, high, and medium flooding.

## Processing

Since FSI is provided as standalone runs, the [`flood_index_data.py` script](https://github.com/WorldModelers/ModelService/blob/master/Flood-Index-Integration/flood_index_data.py) downloads each file listed in the [MINT metadata file](https://github.com/WorldModelers/ModelService/blob/master/Flood-Index-Integration/Flood-Files.csv), stores it to S3 and captures metadata to Redis for each run. 

Then, the [`flood_index_processing.py` script] takes these downloaded files, converts them from NetCDF to point based data and stores them to PostGres. This script also manages the monthly aggregation.

## Issues/Lessons Learned

- This model is a total black box to Jataware so it is unclear what would be required to execute it within MaaS.
