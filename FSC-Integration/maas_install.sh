# Check out FSC Model and switch to docker branch
git clone https://github.com/mjpuma/FSC-WorldModelers.git
cd FSC-WorldModelers
git checkout docker

# Build container used in maas.
# THIS IS A RATHER LARGE IMAGE AND YOU SHOULD MAKE SURE YOU HAVE 10GB+ IN SPACE
docker build -t fsc/latest .
