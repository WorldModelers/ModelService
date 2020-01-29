# Yield Anomalies Model (LPJmL)

Running `maas_install.sh` directly invokes `yield_anomalies_data.py` and `yield_anomalies_processing.py`. 

`yield_anomalies_data.py` establishes model runs for the 180 available yield anomalies model runs provided by PIK. This script assumes that these runs are already stored in S3 at `world-modelers/results/yield_anomalies_model`.

`yield_anomalies_processing.py` converts all raster files provided into point data and puts them into the MaaS database. This script assumes you have configured your database with `../REST-Server/config.ini` as well as the GADM level 2 world file which can be downloaded [from S3 here](https://world-modelers.s3.amazonaws.com/data/gadm2/gadm2.zip). Unzip this in the directory above (`../gadm2`). This also assumes that you have a directory located within this one called `C2P2_LPJmL_yield_backcasts_2018` which contains the relevant `.tif` files.