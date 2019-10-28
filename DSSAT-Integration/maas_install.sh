# create DSSAT directory 
mkdir ~/dssat
cd ~/dssat

# download data file
wget https://world-modelers.s3.amazonaws.com/data/basedata-20191003.tar.xz
wget https://world-modelers.s3.amazonaws.com/data/ethdata-20191003.tar.xz
wget https://world-modelers.s3.amazonaws.com/data/ssddata-20191003.tar.xz

# download config file
wget https://raw.githubusercontent.com/WorldModelers/ModelService/master/DSSAT-Integration/et_docker.json

# create data volume
docker run -v /data -v $PWD:/userdata --name ethdata debian:stable-slim /bin/bash
docker run --rm --volumes-from ethdata -v ${PWD}:/userdata debian:stable-slim bash -c "apt-get update && apt-get install xz-utils && echo 'making directories...' && mkdir /data/base && mkdir /data/ETH && mkdir /data/SSD && echo '...directories built' && cd /data/base && tar xJvf /userdata/basedata-20191003.tar.xz && cd /data/ETH && tar xJvf /userdata/ethdata-20191003.tar.xz && cd /data/SSD && tar xJvf /userdata/ssddata-20191003.tar.xz"

# pull Docker image
docker pull cvillalobosuf/dssat-pythia:latest