import sys
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

import docker
import re
import configparser
import redis
import os
import shutil
import time
import logging
import boto3
import json
import psycopg2
import csv
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime, timedelta

def run_dssat(config, output_path):
    """
    Simple function to generate an DSSATController instance and run the model
    """
    dssat = DSSATController(config, output_path)
    return dssat.run_model()


class DSSATController(object):
    """
    A controller to manage DSSAT model execution.
    """

    def __init__(self, model_config, output_path):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.name = 'DSSAT'
        self.model_config = model_config
        self.client = docker.from_env()
        self.containers = self.client.containers
        self.dssat = 'cvillalobosuf/dssat-pythia:latest'
        self.result_path = output_path
        self.result_name = self.model_config['run_id'] 
        self.run_id = self.model_config['run_id']           
        self.bucket = "world-modelers"
        self.key = f"results/dssat_model/{self.result_name}"
        self.entrypoint=f"/app/pythia.sh --clean-work-dir --all /userdata/et_docker.json"
        self.volumes = {self.result_path: {'bind': '/userdata', 'mode': 'rw'}}
        self.volumes_from = "ethdata"
        self.mgmts = ["maize_irrig","maize_rf_0N","maize_rf_highN","maize_rf_lowN"]
        self.success_msg = 'Running simple analytics'

        if self.model_config["management_practice"] == "separate": 
            self.key += ".zip"
        else:
            self.key += ".csv"

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=self.config['REDIS']['HOST'],
                        port=self.config['REDIS']['PORT'],
                        db=self.config['REDIS']['DB'])

        self.descriptions = {'management_practice': {
                                'combined': 'DSSAT run for maize across all management practices',
                                'maize_rf_highN': 'DSSAT run for maize for a high nitrogen management practice',
                                'maize_irrig': 'DSSAT run for maize for an irrigated, high nitrogen management practice',
                                'maize_rf_0N': 'DSSAT run for maize for a subsistence management practice',
                                'maize_rf_lowN': 'DSSAT run for maize for a low nitrogen management practice'
                                    },
                             'features': {
                                'HWAH': 'Harvested weight at harvest (kg/ha)',
                                'HARVEST_AREA': 'Amount of area harvested under all management practices for this point (ha)',
                                'Production': 'Production for the given point/management practice (kg)',
                                'management_practice': 'The management practice for the given record',
                                },
                             'parameters': {
                                'samples':'integer',
                                'start_year': 'integer',
                                'number_years': 'integer',
                                'management_practice': 'string',
                                'rainfall': 'float',
                                'fertilizer': 'integer',
                                'planting_start': 'string',
                                'planting_end': 'string'
                                },
                             'encoding': {
                                'maize_rf_highN': 1,
                                'maize_irrig': 2,
                                'maize_rf_0N': 3,
                                'maize_rf_lowN': 4
                                }
                            }

        logging.basicConfig(level=logging.INFO)


    def update_config(self):
        """
        Update et_docker.json file with user-submitted config
        """
        with open(f"{self.result_path}/et_docker.json", "r") as f:
            config = json.loads(f.read())
            f.close()

        # If a number of samples is provided, use that
        if self.model_config["samples"] > 0:
            config["sample"] = self.model_config["samples"]
        else:
            # Otherwise, remove the `sample` key and run the 
            # entire region (Ethiopia)
            if "sample" in config:
                config.pop("sample")
        
        # Only produce a combined output if the configuration specifies to do so
        if self.model_config["management_practice"] == "combined":
            config["analytics_setup"]["singleOutput"] = True
        else:
            config["analytics_setup"]["singleOutput"] = False

        ########### SET STARTING YEAR AND NUMBER YEARS ###############
        start_year = 1984
        # Update start year and number of years (if set in the user config)
        if "start_year" in self.model_config:
            start_year = int(self.model_config["start_year"])
            config["default_setup"]["startYear"] = start_year

            # We only bother setting number of years *if* start_year was specified
            if "number_years" in self.model_config:
                number_years = int(self.model_config["number_years"])
                # ensure that the number of years to run does not exceed 2018
                # valid example:
                # start_year = 2017
                # number_years = 2
                # so the model will run for 2 years (2017 and 2018)
                if start_year + number_years - 1 > 2018:
                    # ensure that number_years includes 2018 in this case
                    number_years = 2018 - start_year + 1
            else:
                number_years = 2018 - start_year + 1
            config["default_setup"]["nyers"] = number_years

        # Otherwise default to a 1984 start year and run through 2018
        else:
            config["default_setup"]["startYear"] = start_year
            config["default_setup"]["nyers"] = 35

        config["default_setup"]["sdate"] = f"{start_year}-01-01"

        ########### SET PLANTING START AND END DATES ###############
        if "planting_start" in self.model_config:
            # set the planting start date
            planting_start = self.model_config['planting_start']
            config["default_setup"]["pfrst"] = f"{start_year}-{planting_start}"

        if "planting_start" in self.model_config and "planting_end" in self.model_config:
            # set the planting end date (if a planting start AND end was set)
            planting_end = self.model_config['planting_end']
            config["default_setup"]["plast"] = f"{start_year}-{planting_end}"            

        if "planting_start" in self.model_config and "planting_end" not in self.model_config:
            # if planting_start date but no planting_end date 
            # then default to start date plus 3 months
            plast_month = int(planting_start.split('-')[0]) + 3
            plast_day = int(planting_start.split('-')[0])
            plast_month = "{:02d}".format(plast_month)
            plast_day = "{:02d}".format(plast_day)
            config["default_setup"]["plast"] = f"{start_year}-{plast_month}-{plast_day}"
        
        if "planting_start" not in self.model_config:
            # if no planting start date then we should just use the defaults
            # which correspondes to March 1 through May 20
            config["default_setup"]["pfrst"] = f"{start_year}-03-01"
            config["default_setup"]["plast"] = f"{start_year}-05-20"

        ########### SET FERTILIZER ###############
        if "fertilizer" in self.model_config:
            # Modified fertilizer total adjustment from the baseline amount
            # where the baseline is 100 so anything above 100 is a modification upward
            # and below 100 is modification downward in kg/ha
            config["default_setup"]["fen_tot"] = self.model_config["fertilizer"]
        else:
            config["default_setup"]["fen_tot"] = 100.0

        ########### SET RAINFALL ###############
        if "rainfall" in self.model_config:
            # erain variable should take the form "M0.25" 
            # which indicates 25% normal rainfall or "M1.25" 
            # which indicates 125% normal rainfall
            rain = self.model_config["rainfall"]
            rain = "M{:.2f}".format(rain)
            config["default_setup"]["erain"] = rain
        else:
            config["default_setup"]["erain"] = "M1.00"

        with open(f"{self.result_path}/et_docker.json", "w") as f:
            f.write(json.dumps(config))
            f.close()


    def run_model(self):
        """
        Run DSSAT model inside Docker container
        """
        self.update_config()
        time.sleep(3)
        logging.info(f"Running model run with ID: {self.run_id}")
        try:
            self.model = self.containers.run(self.dssat, 
                                             volumes=self.volumes, 
                                             volumes_from=self.volumes_from,
                                             entrypoint=self.entrypoint,
                                             detach=False,
                                             name='dssat')
            run_logs = self.model.decode('utf-8')

            if self.success_msg in run_logs:
                logging.info("Model run: SUCCESS")
                try:
                    self.storeResults()
                    logging.info("Model output: STORED")
                    try:
                        self.ingest2db()
                        # Success case requires storage to S3 AND ingest to DB
                        # if Success, update Redis accordingly
                        self.r.hmset(self.run_id, 
                            {'status': 'SUCCESS',
                             'bucket': self.bucket,
                             'key': self.key}
                             )                        
                    except Exception as e:
                        msg = f'DB ingest failure: {e}.'
                        logging.error(msg)
                        self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})                        
                except Exception as e:
                    msg = f'Output storage failure: {e}.'
                    logging.error(msg)
                    self.r.hmset(self.run_id, {'status': 'FAIL', 'output': msg})
            else:
                logging.error(f"Model run FAIL: {run_logs}")
                self.r.hmset(self.run_id, {'status': 'FAIL', 'output': run_logs})
        except Exception as e:
            logging.error(f"Model run FAIL: {e}")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})

        # Prune old containers
        prior_container = self.containers.get('dssat')
        prior_container.remove()


    def storeResults(self):
        out = f"{self.result_path}/out"
        result = f"{self.result_path}/{self.result_name}"
        exists = os.path.isdir(out)
        logging.info(exists)
        if exists:
            
            # If separate (all management practices in separate files)
            if self.model_config["management_practice"] == "separate":            
                # Make results for run_id
                os.mkdir(f"{self.result_path}/{self.result_name}")

                # Copy pp_* files to results directory
                for m in self.mgmts:
                    shutil.copy(f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv",
                                f"{result}/pp_{m}.csv")
                shutil.make_archive(result, 'zip', result)
                to_upload = f"{result}.zip"
            
            
            # If combined (one single output file)
            elif self.model_config["management_practice"] == "combined":
                # Copy pp.csv file to results directory
                shutil.copy(f"{self.result_path}/out/eth_docker/test/pp.csv",
                            f"{result}.csv")
                to_upload = f"{result}.csv"
                
            # Otherwise, provide just the management practice of interest
            else:
                m = self.model_config["management_practice"]
                shutil.copy(f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv",
                            f"{result}.csv")
                to_upload = f"{result}.csv"    
                    
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(to_upload, 
                           self.bucket, 
                           self.key, 
                           ExtraArgs={'ACL':'public-read'})
            logging.info(f'Results stored at : https://s3.amazonaws.com/world-modelers/{self.key}')
            return "SUCCESS"
        else:
            return result


    def ingest2db(self):
        init_db()

        # Load Admin2 shape from GADM
        logging.info("Loading GADM shapes...")
        admin2 = gpd.read_file(f"{self.config['GADM']['GADM_PATH']}/gadm36_2.shp")
        admin2['country'] = admin2['NAME_0']
        admin2['state'] = admin2['NAME_1']
        admin2['admin1'] = admin2['NAME_1']
        admin2['admin2'] = admin2['NAME_2']
        admin2 = admin2[['geometry','country','state','admin1','admin2']]

        # Add metadata object to DB
        # TODO: add run_label and run_description
        logging.info("Storing metadata...")
        meta = Metadata(run_id=self.run_id, 
                        model=self.name,
                        run_description=self.descriptions['management_practice'][self.model_config['management_practice']],
                        raw_output_link= f'https://s3.amazonaws.com/world-modelers/{self.key}',
                        # 5 arc minutes (~10km)
                        point_resolution_meters=10000) 
        logging.info("Storing metadata...")
        db_session.add(meta)
        db_session.commit()

        # Add parameters to DB
        logging.info("Storing parameters...")
        for param_name, param_val in self.model_config.items():
            if param_name == 'run_id':
                pass
            else:
                param = Parameters(run_id=self.run_id,
                                  model=self.name,
                                  parameter_name=param_name,
                                  parameter_value=param_val,
                                  parameter_type=self.descriptions['parameters'][param_name])
                db_session.add(param)
                db_session.commit()

        # Process CSV and normalize it
        logging.info("Processing points...")

        # get result file path
        if self.model_config["management_practice"] == "combined":
            # combined CSV
            path = f"{self.result_path}/out/eth_docker/test/pp.csv"
        else:
            # individual management practices
            m = self.model_config["management_practice"]
            path = f"{self.result_path}/out/eth_docker/test/{m}/pp_{m}.csv"

        df = pd.read_csv(path, index_col=False)
        df['latitude'] = df['LATITUDE']
        df['longitude'] = df['LONGITUDE']
        df['geometry'] = df.apply(lambda x: Point(x.longitude, x.latitude), axis=1)
        df['year'] = df['HDAT'].apply(lambda x: int(str(x)[:4]))
        df['days'] = df['HDAT'].apply(lambda x: int(str(x)[4:]))
        df['datetime'] = df.apply(lambda x: datetime(x.year, 1, 1) + timedelta(x.days - 1), axis=1)
        df['run_id'] = self.run_id
        df['model'] = self.name
        df['Production'] = df['HWAH'] * df['HARVEST_AREA']

        # for combined runs only we need to convert the run name to an encoded 
        # float so that it can go into the database
        if 'RUN_NAME' in df:
            df['management_practice'] = df['RUN_NAME'].apply(lambda x: self.descriptions['encoding'][x])

        gdf = gpd.GeoDataFrame(df)

        # Spatial merge on GADM to obtain admin areas
        gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')

        base_cols = ['run_id','model','latitude','longitude',
                     'datetime','admin1','admin2','state',
                     'country']

        feature_cols = ['feature_name','feature_description','feature_value']

        # Need to iterate over features to generate one GDF per feature
        # then upload the GDF per feature to ensure that rows are added for each
        # feature
        for feature_name, feature_description in self.descriptions['features'].items():
            # specific handling for "combined" file
            if feature_name == 'management_practice':
                if self.model_config["management_practice"] != "combined":
                    # if not a combined file, then just move onto the next 
                    # in the for loop and do nothing for this feature_name
                    continue
            cols_to_select = base_cols + [feature_name]
            gdf_ = gdf[cols_to_select] # generate new interim GDF
            gdf_['feature_name'] = feature_name
            gdf_['feature_description'] = feature_description
            gdf_['feature_value'] = gdf_[feature_name]
            gdf_ = gdf_[base_cols + feature_cols]

            # perform bulk insert of entire geopandas DF
            logging.info(f"Storing point data output for {feature_name}...")
            db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
            db_session.commit()            