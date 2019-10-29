# Running Kimetrica's Malnutrition Model
To run any Kimetrica model, you must first build Kimetrica's KiLuigi scheduler and database Docker containers. To do this, run:

```
git clone --recursive https://gitlab.kimetrica.com/DARPA/darpa.git
cd darpa/kiluigi
git checkout master
cd ..

sed -i '4s/kiluigi\///g' env.example
cp env.example kiluigi/.env
cp luigi.cfg.example luigi.cfg
cd kiluigi
sed -i '56s/1000M/10000M/' docker-compose.yml
docker-compose run --entrypoint=bash scheduler
```
This may take some time as the containers are large and complex to build. Also, note that this script may break if the `docker-compose.yml` file changes or if the `env.example` files change.

This is because `sed` is used to replace certain things in these files. In `env.example` `sed` is used to remove `kiluigi` from the path on line 4 since the `docker-compose` command will be run from the `kiluigi` directory.

In the `docker-compose.yml` file, `sed` is used to up the memory limits to 10G (10000M) for the Kiluigi scheduler container so that it does not fail on memory intensive tasks.

The script above should have dropped you into the built scheduler container. Once in the container run:

```
luigi --module models.malnutrition_model.tasks models.malnutrition_model.tasks.MalnutritionGeoJSON --local-scheduler
```

# Updating the Docker Containers
You'll need to remove the old containers and rebuild the Docker containers. To do this you could use:

```
docker ps -a | grep "drp" | awk '{print $1}' | xargs docker rm
```

Which will remove any container matching `drp`. You can then remove the images and rebuild the containers.