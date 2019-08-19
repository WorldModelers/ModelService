# DSSAT Docker Build

## Building the data volume:

1. Download the `ethdata.tar.xz` file from [https://data.agmip.org/darpa/ethdata.tar.xz](https://data.agmip.org/darpa/ethdata.tar.xz)
2. `docker run -v /data/ETH -v $PWD:/userdata --name ethdata debian:stable-slim /bin/bash`
3. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata debian:stable-slim bash -c "apt-get update && apt-get install xz-utils && cd /data/ETH && tar xJvf /userdata/ethdata.tar.xz"`

## Running pythia:

1. Put the JSON file included inside a working directory in your host computer
2. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/pythia --help` (should show the pythia help)
3. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/pythia --setup /userdata/et_docker.json`

## Running DSSAT

1. Put the `DSSAT_pixel_runner.py` script in the same directory as the data and JSON file.
2. Run `python DSSAT_pixel_runner.py` which will generate `summary.csv` files for each pixel.

## Running pythia again:

2. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/pythia --analyze et_docker.json`
3. This will produce the output csv files.