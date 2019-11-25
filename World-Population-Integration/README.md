# WorldPop Africa Population Estimates

Running `maas_install.sh` directly invokes `world_population_data.py` and `world_population_processing.py`. 

`world_population_data.py` establishes model runs for the five time steps (2000-2020 in five-year intervals) available from worldpop. This script assumes that these runs are already stored in S3 at `world-modelers/results/world_population_africa`.

`world_population_processing.py` converts all raster files provided into point data and puts them into the MaaS database. This script assumes you have configured your database with `../REST-Server/config.ini` as well as the GADM level 2 world file which can be downloaded [from S3 here](https://world-modelers.s3.amazonaws.com/data/gadm2/gadm2.zip). Unzip this in the directory above (`../gadm2`). This also assumes that you have a directory located within this one called `Africa_1km_Population` which contains the relevant `.tif` files.
