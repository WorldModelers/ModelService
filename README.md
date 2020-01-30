# MaaS: the Models as a Service API
The goal of the Models as a Service (MaaS) project is to provide an easy to use, descriptive middleware layer API to facilitate model search and discovery, exploration, configuration, and execution. MaaS support an array of agricultural, economic, hydrological, weather, and health models. MaaS provides two key innovations: 

1. MaaS allows users to to work with a **single lightweight and well-documented API** to execute a variety of models
2. MaaS extracts model output from various proprietary or complex formats and provides it to users in a **normalized, tabular format** 

<img src="images/MaaS-Dashboard.png" alt="MaaS Dashboard"
	title="MaaS Dashboard" height="450"/>
	
MaaS allows users to interact with a variety of expert models across a wide ranging parameter space, enabling the creation of sophisticated sensitivity analyses such as the one above, which was made using a 3rd party tool, but powered by MaaS. 

## Contents

- [Design](#design)
- [Available Models](#available-models)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Collaborators](#collaborators)

## Design

#### Model discovery
Model exploration is managed through the [`Exploration Controller`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/controllers/exploration_controller.py). The `Exploration Controller` allows a user to obtain a model's description, understand its parameters, obtain an example/default configuration, and understand its outputs.

This is further enabled through the [`Concepts Controller`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/controllers/concepts_controller.py) which maps `concepts` to models, model outputs, and model parameters. A client may request a list of all concepts that are mapped to models in MaaS and may submit a single concept to learn which related models, outputs and parameters are tied to it in MaaS. This is powered by [Eidos](https://github.com/clulab/eidos), an open-domain machine reading system designed by the [Computational Language Understanding (CLU) Lab](http://clulab.cs.arizona.edu/) at [University of Arizona](http://www.arizona.edu/).

#### Model execution
Model execution is managed by the [`Execution Controller`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/controllers/execution_controller.py). Models consist of pre-built Docker images that are hosted on an arbitrary server. Running a model requires the creation of a specific model controller, such as this one for [Kimetrica's malnutrition model](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/kimetrica.py). The model controller is responsible for obtaining a model configuration and tasking Docker to run the model image inside a container with the given configuration. The model controller specifies a Docker container entrypoint, such as [this one](https://github.com/WorldModelers/ModelService/blob/master/Kimetrica-Integration/run.py). The model controller is then responsible for storing the output results file(s) to S3 and ingesting the normalized results into the MaaS database.

Models may be run using the `/run_model` endpoint. For more information on model execution, refer to [`docs/model-execution.md`](https://github.com/WorldModelers/ModelService/blob/master/docs/model-execution.md).
 
## Available Models
Currently, MaaS supports the following models:

| Team      | Category     | Model                                | Description                                                             | 
|-----------|--------------|--------------------------------------|-------------------------------------------------------------------------| 
| Atlas AI  | Demographic  | Asset Wealth Model                   | Asset levels for 2003 to 2018                                           | 
| Atlas AI  | Demographic  | Consumption Model                    | Household consumption for 2003 to 2018                                  | 
| Atlas AI  | Agricultural | Atlas AI CropLand Use Model          | Probability estimates of whether land is cropped at 480m res.           | 
| UCSB      | Weather      | CHIRPS                               | Rainfall levels and anomalies for 2008 through end of March 2018        | 
| UFL       | Agricultural | DSSAT                                | Maize, teff, sorghum, and wheat yields from 1984 through 2017         | 
| MINT      | Hydrology    | Flood Severity Index Model           | Days with flooding for a given month for 2008 to 2017                   | 
| MINT      | Hydrology    | PIHM                                 | Water height for 2008 onwards for various basins                        | 
| MINT      | Hydrology    | Topoflow                             | Water heights for various basins                                        | 
| Kimetrica | Demographic  | Kimetrica Population Model           | Ethiopia population from 2000 onward                                    | 
| Kimetrica | Demographic  | Kimetrica Malnutrition model         | Malnutrition cases 2007 to 2018                                         | 
| Kimetrica | Economic     | Kimetrica Market Price Model         | Commodity pricing for SS and Ethiopia 2017-2018                         | 
| Columbia  | Economic     | Food Shocks Cascade                  | Induce a regional shock to wheat production                             | 
| Columbia  | Agricultural | AgMIP’s Seasonal Crop Yield Emulator | Percent yield anomalies from detrended 1980 - 2010 mean                       | 
| CSIRO     | Agricultural | APSIM                                | Multiple scenarios (rain, temp, irrigation, fertilizer, etc) for 2018 | 
| CSIRO     | Agricultural | G-Range                              | Multiple scenarios (rain, temp, irrigation, fertilizer, etc) for 2018 | 
| CSIRO     | Agricultural | CLEM                                 | Sales and demand for multiple crops at the farm level                   | 
| PIK       | Agricultural | Yield Anomalies LPJmL                | Yield anomalies from 1984 through April 2018                            | 
| PIK       | Agricultural | LPJmL 2018                           | Crop production projections for 2018                                    | 
| PIK       | Agricultural | LPJmL Historic                       | Historic crop production from 1984 to 2017                              | 
| PIK       | Economic     | Multi TWIST                          | Global wheat prices for various scenarios 1980 to 2017                  | 
| N/A       | Demographic  | World Pop                            | Ethiopia population from 2000 onward, in 5 year intervals             | 


## Architecture

![MaaS Architecture](images/MaaS-Architecture.png "MaaS Architecture")

## Documentation

Documentation on setup and installation, as well as usage, can be found in the [`docs/`](docs).

## Collaborators

MaaS collaborators include:

* [Atlas AI](https://www.atlasai.co/)
* [UCSB](https://ucsb.edu)
* [University of Florida](https://ufl.edu)
* [USC Information Sciences Institute](https://www.isi.edu/)
* [Penn State](https://psu.edu)
* [Kimetrica](https://kimetrica.com/)
* [Columbia University](https://www.columbia.edu/)
* [CSIRO](https://www.csiro.au/)
* [Potsdam Institute for Climate Impact Research](https://www.pik-potsdam.de/pik-frontpage)