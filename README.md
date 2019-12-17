# ModelService
This repository contains the Models as a Service (MaaS) API for World Modelers.
## Contents

- [Design](#design)
	- [Project Goals](#project-goals)
	- [Architecture](#architecture)
- [Development](#development)
	- [Installation](#installation)
	- [Swagger Editor](#swagger-editor)
	- [Open API Code Generation](#open-api-code-generation)
	- [Running the REST Server](#running-the-rest-server)

## Design

### Project Goals
The goal of this project is to provide an easy to use, descriptive middleware layer API to facilitate model search and discovery, exploration, configuration, and execution. 

#### Model discovery
Model exploration is managed through the [`Exploration Controller`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/controllers/exploration_controller.py). The `Exploration Controller` allows a user to obtain a model's description, understand its parameters, obtain an example/default configuration, and understand its outputs.

This is further enabled through the `Concepts Controller` which maps `concepts` to models, model outputs, and model parameters. A client may request a list of all concepts that are mapped to models in MaaS and may submit a single concept to learn which related models, outputs and parameters are tied to it in MaaS.

#### Model execution
Model execution is managed by the [`Execution Controller`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/controllers/execution_controller.py). Models consist of pre-built Docker images that are hosted on an arbitrary server. Running a model requires the creation of a specific model controller, such as this one for [Kimetrica's malnutrition model](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/kimetrica.py). The model controller is responsible for obtaining a model configuration and tasking Docker to run the model image inside a container with the given configuration. The model controller specifies a Docker container entrypoint, such as [this one](https://github.com/WorldModelers/ModelService/blob/master/Kimetrica-Integration/run.py) which is responsible for writing the model output (from within the container) to S3.

Models may be run using the `/run_model` endpoint. Descriptions of model configurations can be found in [`docs/model-execution.md`](https://github.com/WorldModelers/ModelService/blob/master/docs/model-execution.md). Currently, MaaS supports the following models:

- Kimetrica Population Model
- Kimetrica Malnutrition Model
- Food Shocks Cascade Model
- DSSAT
- Atlas.ai Consumption Model
- Atlas.ai Asset Wealth Model
- CHIRPS
- CHIRPS-GEFS
- LPJmL Yield Anomalies
- World Pop Africa
- Flood Severity Index Model


### Architecture

![MaaS Architecture](images/MaaS-Architecture.png "MaaS Architecture")


## Development

### Installation and Set Up

#### Building the models

First, you must install the various models:

```
# SET $HOME/.aws/credentials to proper key and secret.

# Install MAAS
git clone https://github.com/WorldModelers/ModelService.git
cd ModelService/REST-Server
conda create -n maas_env python=3.7 pip jupyter -y
source activate maas_env

# Install GDAL dependencies
sudo add-apt-repository ppa:ubuntugis/ppa && sudo apt-get update
sudo apt-get update
sudo apt-get install python3.6-dev
sudo apt-get install gdal-bin
sudo apt-get install libgdal-dev
sudo apt install python3-rtree

# GDAL bindings
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal

pip install -r requirements.txt

# Install FSC Model.  You will get prompted for github credentials.
# This will take quite a bit of time.
cd ../FSC-Integration/
./maas_install.sh

# Install Kimetrica Model.
cd ../../Kimetrica-Integration/

# Please look at this file as you must set the CKAN creds manually right now...
./maas_install.sh

# Install DSSAT
cd ../DSSAT-Integration
./maas_install.sh

# Install Atlas
cd ../Atlas-Integration
./maas_install.sh

# Install Yield Anomalies Model
cd ../Yield-Anomalies-Integration
./maas_install.sh

# Install World Population Africa Model
cd ../World-Population-Integration
./maas_install.sh

# Install Flood Severity Index
cd ../Flood-Index-Integration
./maas_install.sh
```

#### Redis Set-up
In production, MaaS relies on an AWS hosted Redis instance. For development, you can download a sample Redis dump with:

```
wget https://world-modelers.s3.amazonaws.com/data/redis-11-11-2019.rdb]
mv redis-11-11-2019.rdb dump.rdb
```

Then you can turn on Redis using the `docker-compose` file in the base of this repository. You can do this with `docker-compose up -d` (assumes you have Docker installed and running). This will run Redis on port `6379`.

#### RQ Worker

Models are executed asynchronously using [RQ](https://python-rq.org). This requires that an RQ worker is running. You can do this in a screen session from the `REST-Server` directory with:

```
screen -S RQ
```

This will generate a screen session named RQ. You should then run the worker with:

```
rq worker high default low -u redis://localhost:6379/0
```

This will set the worker to listen to the queues called `high` and `low` as well as the `default` queue using a Redis instance running at `localhost`. For production this should be replaced with the URL for the production Redis instance.

#### Running MaaS

Run MaaS from the `REST-Server` directory with:

```
cd ../../REST-Server
python -m openapi_server
```

### Swagger Editor
To use this, run the following:

```
docker pull swaggerapi/swagger-editor:latest
docker run -d -p 80:8080 swaggerapi/swagger-editor
```

This will run Swagger Editor (in detached mode) on port 80 on your machine, so you can open it by navigating to http://localhost in your browser.

### Open API Code Generation

Unfortunately, the current Swagger Editor does not support code gen for Open API 3.0 and Flask. To generate the server stub use:

```
wget http://central.maven.org/maven2/org/openapitools/openapi-generator-cli/3.3.4/openapi-generator-cli-3.3.4.jar -O openapi-generator-cli.jar

java -jar openapi-generator-cli.jar generate \
  -i model_service_api.yaml \
  -l python-flask \
  -o Rest-Server-UPDATE
```

### Running the REST Server
First navigate to the `REST-Server` directory with `cd REST-Server`. Next, install the requirements with something like:

```
pip3 install -r requirements.txt
```

Now you can run the server with `python3 -m openapi_server`. You can access the UI at [http://0.0.0.0:8080/ui](http://0.0.0.0:8080/ui).

### Results Storage
You must ensure that the results stored by the model are readable and writable by the process running the server. This location is defined in `config.ini`. For example, for FSC in production this could look like:

```
[FSC]
OUTPUT_PATH = /home/ubuntu/ModelService/results/fsc/outputs
```

However you must ensure that this location is readable and writable by the process running the server. Results will be written by the model's Docker container (which may be `root`) so you likely need to `sudo chmod -r +777 /home/ubuntu/ModelService/results` or something like that to ensure appropriate permissions are set.
