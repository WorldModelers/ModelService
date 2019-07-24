git clone --recursive https://gitlab.kimetrica.com/DARPA/darpa.git
cd darpa/kiluigi
git checkout master
cd ..

sed -i '4s/kiluigi\///g' env.example
cp env.example kiluigi/.env
cp luigi.cfg.example luigi.cfg
cd kiluigi
sed -i '58s/1000M/10000M/' docker-compose.yml
cd ../../
cp run.py darpa/
cd darpa/kiluigi
docker-compose run --entrypoint=bash scheduler
