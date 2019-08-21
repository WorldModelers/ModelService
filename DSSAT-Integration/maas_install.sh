# create DSSAT directory 
mkdir ~/dssat-docker
cd ~/dssat-docker

# download data file
wget https://world-modelers.s3.amazonaws.com/data/ethdata.tar.xz

# download config file
wget https://raw.githubusercontent.com/WorldModelers/ModelService/master/DSSAT-Integration/et_docker.json

# create data volume
docker run -v /data/ETH -v $PWD:/userdata --name ethdata debian:stable-slim /bin/bash
docker run --rm --volumes-from ethdata -v ${PWD}:/userdata debian:stable-slim bash -c "apt-get update && apt-get install xz-utils && cd /data/ETH && tar xJvf /userdata/ethdata.tar.xz"