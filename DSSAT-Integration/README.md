# DSSAT Docker Build

## Building the data volume:

1. Download the `ethdata.tar.xz` file from [https://world-modelers.s3.amazonaws.com/data/ethdata.tar.xz](https://world-modelers.s3.amazonaws.com/data/ethdata.tar.xz)
2. `docker run -v /data/ETH -v $PWD:/userdata --name ethdata debian:stable-slim /bin/bash`
3. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata debian:stable-slim bash -c "apt-get update && apt-get install xz-utils && cd /data/ETH && tar xJvf /userdata/ethdata.tar.xz"`

## Running pythia:

1. Put the JSON file included inside a working directory in your host computer
2. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/pythia --help` (should show the pythia help)
3. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/pythia --setup /userdata/et_docker.json`

## Running DSSAT

1. `docker run --rm --volumes-from ethdata -v ${PWD}:/userdata cvillalobosuf/dssat-pythia:develop --all /userdata/et_docker.json`
2. This step produces a `pp_{practice_name}.csv` results file in each of the management practices directory.