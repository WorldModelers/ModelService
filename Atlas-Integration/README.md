# Setting up Atlas.ai 

You should ensure that the `DATA_PATH` in `config.ini` matches whatever you set as the `output_directory` when you run `atlas_data.py`.

Also, ensure that `URL` in `config.ini` matches your development or production server (e.g. `http://localhost:8080` or `https://model-service.worldmodelers.com`).

`maas_install.sh` also runs `atlas_processing.py` which assumes you have configured your database with `../REST-Server/config.ini` as well as the GADM level 2 world file which can be downloaded [from S3 here](https://world-modelers.s3.amazonaws.com/data/gadm2/gadm2.zip). Unzip this in the directory above (`../gadm2`). This also assumes that you have a directory located within this one called `data` which contains the relevant `.tif` files.