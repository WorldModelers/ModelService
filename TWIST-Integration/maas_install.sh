# Check out TWIST Model and switch to docker branch
git clone https://github.com/cstotto/multi_twist.git multi_twist
cd multi_twist
git checkout production_shock_docker_version

# Build container used in maas.
docker build -f Dockerfile . -t multi_twist