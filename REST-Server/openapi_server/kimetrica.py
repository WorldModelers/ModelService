import sys
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

import docker
import re
import configparser
import redis
import time
import logging
import geopandas as gpd
from database import init_db, db_session
from models import Metadata, Output, Parameters
from openapi_server.util import raster2gpd
import datetime
import calendar

def run_kimetrica(config):
    """
    Simple function to generate an KiController instance and run the model
    """
    kimetrica = KiController(config)
    return kimetrica.run_model()

class KiController(object):
    """
    A controller to manage Kimetrica model execution.
    """

    def __init__(self, model_config):
        self.bucket = "world-modelers"
        self.model_config = model_config
        self.year = self.model_config['config'].get('year', 2018)
        self.month = self.model_config['config'].get('month', 1)
        self.start_time = datetime.datetime(year=self.year, month=self.month, day=1)
        self.start_time_f = self.start_time.strftime("%Y-%m-%d")
        self.end_time_f = self.add_one_month(self.start_time)
        # Rework this all later by pulling from yml or other config.  For now this works...
        self.model_map = {
		"malnutrition_model":{
			"key":"results/malnutrition_model/" + model_config["config"]["run_id"] + ".tiff",
			"entrypoint":f"python run.py --bucket={self.bucket} --model_name=malnutrition_model"\
                          " --task_name=HiResRasterMasked --result_name=intermediate/*HiResRasterMasked*/*.pickle/*tiff"\
                          " --key=" + "results/malnutrition_model/" + model_config["config"]["run_id"] + ".tiff "\
                           + f"--params time|{self.start_time_f}-{self.end_time_f}|rainfall-scenario|"\
                           + str(model_config["config"].get("rainfall_scenario",""))\
                           + f"|country-level|'{model_config['config'].get('country','Ethiopia')}'"\
                           + f"|geography|/usr/src/app/models/geography/boundaries/{model_config['config'].get('country','Ethiopia').replace(' ','_').lower()}_2d.geojson|rainfall-scenario-geography|/usr/src/app/models/geography/boundaries/{model_config['config'].get('country','Ethiopia').replace(' ','_').lower()}_2d.geojson",
            "feature_name": "malnutrition cases",
            "feature_description": "predicted number of malnutrition cases (Global Acute Malnutrition)",
            "band": 2
				    },  
        "population_model":{
			"key":"results/population_model/" + model_config["config"]["run_id"] + ".tiff",
            "entrypoint":f"python run.py --bucket={self.bucket} --model_name=population_model"\
                          " --task_name=HiResPopRasterMasked --result_name=intermediate/*HiResPopRasterMasked*/*.pickle/*.tiff"\
                          " --key=" + "results/population_model/" + model_config["config"]["run_id"] + ".tiff "\
                          + f"--params time|{self.year}-01-01-{int(self.year) + 1}-01-01|" + f"country-level|'{model_config['config'].get('country','Ethiopia')}'"\
                          + f"|geography|/usr/src/app/models/geography/boundaries/{model_config['config'].get('country','Ethiopia').replace(' ','_').lower()}_2d.geojson|rainfall-scenario-geography|/usr/src/app/models/geography/boundaries/{model_config['config'].get('country','Ethiopia').replace(' ','_').lower()}_2d.geojson",
            "feature_name": "population",
            "feature_description": "population estimate at 1km^2 grid cell",
            "band": 1
				   }
        }
        config = configparser.ConfigParser()
        config.read('config.ini')
        logging.basicConfig(level=logging.INFO)
        
        self.install_path = config["MALNUTRITION"]["INSTALL_PATH"]
        self.s3_cred_path = config["MALNUTRITION"]["S3_CRED_PATH"]
        
        self.run_id = self.model_config['config']['run_id'] 
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.scheduler = 'drp_scheduler'
        self.db = 'drp_db'
        self.db_name = 'kiluigi-db'
        self.success_msg = 'This progress looks :)'
        
        # These are now pulled from model_map above
        self.name = self.model_config["name"]
        self.key = self.model_map[model_config["name"]]["key"]
        self.feature_description = self.model_map[model_config["name"]]["feature_description"]
        self.feature_name = self.model_map[model_config["name"]]["feature_name"]
        self.band = self.model_map[model_config["name"]]["band"]
        self.run_description = f"Run of Kimetrica {self.name}."
        self.key = self.model_map[model_config["name"]]["key"]
        self.entrypoint=self.model_map[model_config["name"]]["entrypoint"]

        self.volumes = {self.s3_cred_path:{'bind':'/root/.aws','mode':'rw'},self.install_path: {'bind': '/usr/src/app', 'mode': 'rw'}}
        self.environment = self.parse_env_file(self.install_path + '/kiluigi/.env')
        self.db_ports = {'5432/tcp': 5432}
        self.network_name = "kiluigi"
        self.environment['PYTHONPATH'] = '/usr/src/app:/usr/src/app/kiluigi'
        self.db_environment = {"APP": self.environment["APP"],
                          "ENV": self.environment["ENV"],
                          "PGPASSWORD": self.environment["PGPASSWORD"],
                          "POSTGRES_PASSWORD": self.environment["PGPASSWORD"]}
        self.network = self.create_network()
        self.db_container = self.run_db()
        self.gadm = config['GADM']['GADM_PATH']

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=config['REDIS']['HOST'],
                        port=config['REDIS']['PORT'],
                        db=config['REDIS']['DB'])          


    def parse_env_file(self, path_to_file):
        """
        Parse a Kimetrica .env file into a dictionary
        Ultimately this should be deprecated in favor of
        a better approach to storing and loading environment variables
        and configurations for Kimetrica models executions.
        """
        envre = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')
        env_var = re.compile(r'\$\{[0-9a-zA-Z_]*\}')
        alpha_num = re.compile(r'[0-9a-zA-Z_]+')
        result = {}
        with open(path_to_file) as ins:
            for line in ins:
                match = envre.match(line)
                if match is not None:
                    key = match.group(1)
                    val = match.group(2)
                    to_replace = env_var.findall(val)
                    for v in to_replace:
                        found = result[alpha_num.search(v).group(0)]
                        val = val.replace(v, found)
                    result[key] = val
        return result


    def create_network(self):
        """
        Establish network for communication between
        Kimetrica Docker containers.
        """
        curr_network = self.client.networks.list(names=[self.network_name])
        if len(curr_network) > 0:
            return curr_network[0]
        else:
            network = self.client.networks.create(self.network_name, driver="bridge")
        return network


    def run_db(self):
        """
        Run KiLuigi Database Docker container.
        """
        try:
            logging.info(f"Obtaining Kimetrica DB")
            db_container = self.containers.get(self.db_name)
        except:
            # db_container does not exist, so we must make it
            logging.info(f"Kimetrica DB doesn't exist: creating it")
            db_container = self.containers.run(self.db,
                                          environment=self.db_environment, 
                                          ports=self.db_ports, 
                                          network=self.network_name, 
                                          name=self.db_name,
                                          detach=True)
        return db_container 


    def run_model(self):
        """
        Run KiLuigi model inside Docker container
        """
        logging.info(f"Running Kimetrica model run with ID: {self.run_id}")
        logging.info(f"Running Kimetrica model run with entrypoint: {self.entrypoint}")
        try:
            self.model = self.containers.run(self.scheduler, 
                                   environment=self.environment, 
                                   volumes=self.volumes, 
                                   network=self.network_name, 
                                   links={self.db_container.short_id: None},
                                   entrypoint=self.entrypoint,
                                   detach=False,
                                   name='kimetrica')
            run_logs = self.model.decode('utf-8')

            if self.success_msg in run_logs:
                try:
                    self.ingest2db()
                except Exception as e:
                    msg = f'DB ingest failure: {e}.'
                    logging.error(msg)
                    self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})  
                logging.info("Model run: SUCCESS")         
                self.r.hmset(self.run_id, 
                    {'status': 'SUCCESS',
                     'bucket': self.bucket,
                     'key': self.key}
                         )
            else:
                logging.error(f"Model run FAIL: {run_logs}")
                self.r.hmset(self.run_id, {'status': 'FAIL', 'output': run_logs})
                
        except Exception as e:
            logging.error(f"Model run FAIL: {e}")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})

        # Prune old containers
        prior_container = self.containers.get('kimetrica')
        prior_container.remove()


    def ingest2db(self):
        init_db()

        # Load Admin2 shape from GADM
        logging.info("Loading GADM shapes...")
        admin2 = gpd.read_file(f'{self.gadm}/gadm36_2.shp')
        admin2['country'] = admin2['NAME_0']
        admin2['state'] = admin2['NAME_1']
        admin2['admin1'] = admin2['NAME_1']
        admin2['admin2'] = admin2['NAME_2']
        admin2 = admin2[['geometry','country','state','admin1','admin2']]

        # Add metadata object to DB
        # TODO: add run_label and run_description
        meta = Metadata(run_id=self.run_id, 
                        model=self.name,
                        run_description=self.run_description,
                        raw_output_link= f'https://s3.amazonaws.com/world-modelers/{self.key}',
                        point_resolution_meters=1000)
        logging.info("Storing metadata...")
        db_session.add(meta)
        db_session.commit()

        # Add parameters to DB
        logging.info("Storing parameters...")
        for param_name, param_val in self.model_config['config'].items():
            if param_name == 'run_id':
                pass
            else:
                if param_name == 'year':
                    param_type = 'integer'
                elif param_name == 'month':
                    param_type = 'integer'
                else:
                    param_type = 'string'

                param = Parameters(run_id=self.run_id,
                                  model=self.name,
                                  parameter_name=param_name,
                                  parameter_value=param_val,
                                  parameter_type=param_type)
                db_session.add(param)
                db_session.commit()

        # Process tiff file into point data
        logging.info("Processing tiff...")
        InRaster = f"{self.install_path}/output/{self.key}"
        feature_name = self.feature_name
        feature_description = self.feature_description
        gdf = raster2gpd(InRaster,feature_name,band=self.band)
        
        # Spatial merge on GADM to obtain admin areas
        gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
        
        # Set run fields: datetime, run_id, model
        gdf['datetime'] = self.start_time
        gdf['run_id'] = self.run_id
        gdf['model'] = self.name
        gdf['feature_description'] = feature_description
        del(gdf['geometry'])
        del(gdf['index_right'])

        # perform bulk insert of entire geopandas DF
        logging.info("Storing point data output...")
        db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
        db_session.commit()

    def add_one_month(self, orig_date):
        # advance year and month by one month
        new_year = orig_date.year
        new_month = orig_date.month + 1
        # note: in datetime.date, months go from 1 to 12
        if new_month > 12:
            new_year += 1
            new_month -= 12
        last_day_of_month = calendar.monthrange(new_year, new_month)[1]
        new_day = min(orig_date.day, last_day_of_month)
        new_date = orig_date.replace(year=new_year, month=new_month, day=new_day)
        return new_date.strftime("%Y-%m-%d")        