# Installation and Set Up

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

# Install UAZ Concept Mapping Service
# This builds the Docker container and runs it and will take a while since
# it requires building Eidos
cd ../UAZ-Integration
./maas_install.sh

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

# Install PIHM
cd ../PIHM-Integration
./maas_install.sh

# Install APSIM and G-Range
cd ../CSIRO-Integration
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

#### DB Setup

You should also ensure that the database is appropriately set up. To do that, you should execute the SQL scripts located in `db/db-setup` against the database.