#!/bin/bash

git clone https://github.com/clulab/eidos.git
cd eidos/Docker
sed -i '36i\RUN git checkout maas' DockerfileRun
docker build -f DockerfileRun . -t eidos-webservice
docker run -id -p 9000:9000 eidos-webservice