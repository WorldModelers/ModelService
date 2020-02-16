---
layout: default
title: Models Overview
nav_order: 8
has_children: true
---

# Models Overview

There are currently 21 models available through MaaS. Each one has required custom integration. For some, this may include simply normalizing the models output. For others, it may have involved Dockerizing the model, writing metadata for the model, as well as output normalization. The goal of these documents is to describe the process Jataware used for integrating each of the models and the lessons learned from each.

> Note: all model execution was disabled for the January, 2020 experiment. When models are described as _executable_ through MaaS, that reflects the current capability, but not was is currently deployed to the MaaS production environment.


## Available Models
Currently, MaaS supports the following models:

| Team      | Category     | Model                                | Description                                                             | 
|-----------|--------------|--------------------------------------|-------------------------------------------------------------------------| 
| Atlas AI  | Demographic  | [**Asset Wealth Model**](AtlasAI.md)                   | Asset levels for 2003 to 2018                                           | 
| Atlas AI  | Demographic  | [**Consumption Model**](AtlasAI.md)                    | Household consumption for 2003 to 2018                                  | 
| Atlas AI  | Agricultural | [**Atlas AI CropLand Use Model**](AtlasAI.md)          | Probability estimates of whether land is cropped at 480m res.           | 
| UCSB      | Weather      | [**CHIRPS**](CHIRPS.md)                               | Rainfall levels and anomalies for 2008 through end of March 2018        | 
| UCSB      | Weather      | [**CHIRPS-GEFS**](CHIRPS.md)                               | Daily near-term ensemble rainfall forecasts        | 
| UFL       | Agricultural | [**DSSAT**](DSSAT.md)                                | Maize, teff, sorghum, and wheat yields from 1984 through 2017         | 
| MINT      | Hydrology    | [**Flood Severity Index Model**](FSI.md)           | Days with flooding for a given month for 2008 to 2017                   | 
| MINT      | Hydrology    | [**PIHM**](PIHM.md)                                 | Water height for 2008 onwards for various basins                        | 
| MINT      | Hydrology    | [**Topoflow**](Topoflow.md)                             | Water heights for various basins                                        | 
| Kimetrica | Demographic  | [**Kimetrica Population Model**](Kimetrica.md)           | Ethiopia population from 2000 onward                                    | 
| Kimetrica | Demographic  | [**Kimetrica Malnutrition model**](Kimetrica.md)         | Malnutrition cases 2007 to 2018                                         | 
| Kimetrica | Economic     | [**Kimetrica Market Price Model**](Kimetrica.md)         | Commodity pricing for SS and Ethiopia 2017-2018                         | 
| Columbia  | Economic     | [**Food Shocks Cascade**](FSC.md)                  | Induce a regional shock to wheat production                             | 
| Columbia  | Agricultural | [**AgMIP’s Seasonal Crop Yield Emulator**](AgMIP.md) | Percent yield anomalies from detrended 1980 - 2010 mean                       | 
| CSIRO     | Agricultural | [**APSIM**](CSIRO.md)                                | Multiple scenarios (rain, temp, irrigation, fertilizer, etc) for 2018 | 
| CSIRO     | Agricultural | [**G-Range**](CSIRO.md)                              | Multiple scenarios (rain, temp, irrigation, fertilizer, etc) for 2018 | 
| CSIRO     | Agricultural | [**CLEM**](CSIRO.md)                                 | Sales and demand for multiple crops at the farm level                   | 
| PIK       | Agricultural | [**Yield Anomalies LPJmL**](LPJmL.md)                | Yield anomalies from 1984 through April 2018                            | 
| PIK       | Agricultural | [**LPJmL 2018**](LPJmL.md)                           | Crop production projections for 2018                                    | 
| PIK       | Agricultural | [**LPJmL Historic**](LPJmL.md)                       | Historic crop production from 1984 to 2017                              | 
| PIK       | Economic     | [**Multi TWIST**](TWiST.md)                          | Global wheat prices for various scenarios 1980 to 2017                  | 
| N/A       | Demographic  | [**World Pop**](external-models.md)                            | Ethiopia population from 2000 onward, in 5 year intervals             | 