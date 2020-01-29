import sys
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

from openapi_server.util import raster2gpd    

import geopandas as gpd
import requests
import logging
import boto3
import os
from pyproj import Proj, transform
import configparser
import redis
from datetime import datetime, timedelta
import json


def run_chirps(name, model_config, output_path):
    """
    Simple function to generate a CHIRPSController instance and run the model
    """
    chirps = CHIRPSController(name, model_config, output_path)
    return chirps.run_model()


class CHIRPSController(object):
    """
    A controller to manage CHIRPS model execution.
    """

    def __init__(self, name, model_config, output_path):
        config = configparser.ConfigParser()
        config.read('config.ini')
        logging.basicConfig(level=logging.INFO)        
        self.name = name
        self.model_config = model_config
        self.run_id = self.model_config['run_id']        
        self.output_path = output_path
        self.bucket = "world-modelers"
        self.dekad = self.model_config["dekad"]
        self.year = self.model_config["year"]
        self._type = self.model_config["_type"]
        self.bbox = self.model_config["bbox"]
        self.min_pt, self.max_pt = self.convert_bbox(self.bbox)
        self.url = f"http://chg-ewxtest.chg.ucsb.edu/proxies/wcsProxy.php?layerNameToUse=chirps:"\
                   f"chirps_africa_1-dekad-{self.dekad}-{self.year}_{self._type}"\
                   f"&lowerLeftXToUse={self.min_pt[0]}&lowerLeftYToUse={self.min_pt[1]}"\
                   f"&upperRightXToUse={self.max_pt[0]}&upperRightYToUse={self.max_pt[1]}"\
                   f"&wcsURLToUse=http://chg-ewxtest.chg.ucsb.edu:8080/geoserver/wcs?&resolution"\
                   f"=0.05&srsToUse=EPSG:3857&outputSrsToUse=EPSG:4326"
        self.url_gefs = f"http://chg-ewxtest.chg.ucsb.edu/proxies/wcsProxy.php?layerNameToUse="\
                        f"chirpsgefslast:chirpsgefslast_africa_1-dekad-{self.dekad}-{self.year}_{self._type}"\
                        f"&lowerLeftXToUse={self.min_pt[0]}&lowerLeftYToUse={self.min_pt[1]}"\
                        f"&upperRightXToUse={self.max_pt[0]}&upperRightYToUse={self.max_pt[1]}"\
                        f"&wcsURLToUse=http://chg-ewxtest.chg.ucsb.edu:8080/geoserver/wcs?&resolution"\
                        f"=0.05&srsToUse=EPSG:3857&outputSrsToUse=EPSG:4326"
        self.result_name = self.model_config['run_id']
        self.key = f"results/chirps/{self.result_name}.tiff"
        self.result_path = output_path
        self.gadm = config['GADM']['GADM_PATH']

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=config['REDIS']['HOST'],
                        port=config['REDIS']['PORT'],
                        db=config['REDIS']['DB'])          

        self.features = {'mm_data': {
                                'feature_name': 'Rainfall',
                                'feature_description': 'rainfall in mm per 5km',
                                'run_description': f'{self.name} rainfall data'
                                    },
                        'mm_anomaly': {
                                'feature_name': 'Rainfall relative to average',
                                'feature_description': 'Rainfall relative to the historic average in mm per 5km',
                                'run_description': f'{self.name} anomaly data'
                                    },
                        'none_z-score': {
                                'feature_name': 'SPI',
                                'feature_description': 'Standardized Precipitation Index',
                                'run_description': f'{self.name} Standardized Precipitation Index data'
                                    }
                        }

    def run_model(self):
        """
        Obtain CHIRPS data
        """
        logging.info(f"Running model run with ID: {self.run_id}")

        try:
            # if CHIRPS-GEFS, use that URL
            if self.name == 'CHIRPS-GEFS':
                data = requests.get(self.url_gefs)

            # otherwise, use CHRIPS URL 
            else:
                data = requests.get(self.url)
                
            logging.info("Model run: SUCCESS")

            with open(f"{self.output_path}/{self.result_name}.tiff", "wb") as f:
                f.write(data.content)

            self.storeResults()
            logging.info("Model output: STORED")

            self.ingest2db()
            logging.info("Model to DB: SUCCESS")

            self.r.hmset(self.run_id, 
                {'status': 'SUCCESS',
                 'bucket': self.bucket,
                 'key': self.key}
                 )
        except Exception as e:
            logging.info(f"Model run FAIL: {e}")
            self.r.hmset(self.run_id, {'status': 'FAIL', 'output': str(e)})


    def convert_bbox(self, bb):
        """
        Convert WGS84 coordinate system to Web Mercator
        Initial bbox is in format [xmin, ymin, xmax, ymax]. 
        x is longitude, y is latitude.
        Output is Web Mercator min/max points for a bounding box.
        """
        in_proj = Proj(init='epsg:4326')
        out_proj = Proj(init='epsg:3857')
        min_pt = transform(in_proj, out_proj, bb[0], bb[1])
        max_pt = transform(in_proj, out_proj, bb[2], bb[3])
        return min_pt, max_pt  
    

    def storeResults(self):
        result = f"{self.result_path}/{self.result_name}.tiff"
        exists = os.path.exists(result)
        logging.info(exists)
        if exists:    
            session = boto3.Session(profile_name="wmuser")
            s3 = session.client('s3')
            s3.upload_file(result, 
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
                        run_description=self.features[self._type]['run_description'],
                        raw_output_link= f'https://s3.amazonaws.com/world-modelers/{self.key}',
                        point_resolution_meters=5000)
        logging.info("Storing metadata...")
        db_session.add(meta)
        db_session.commit()

        # Add parameters to DB
        logging.info("Storing parameters...")
        for param_name, param_val in self.model_config.items():   
            if param_name != 'run_id':             
                if param_name == 'year':
                    param_type = 'integer'
                elif param_name == 'bbox':
                    param_type = 'array'
                    param_val = json.dumps(param_val)
                elif param_name == 'dekad':
                    param_type = 'integer'
                    param_val = int(param_val)
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
        InRaster = f"{self.result_path}/{self.result_name}.tiff"
        feature_name = self.features[self._type]['feature_name']
        feature_description = self.features[self._type]['feature_description']
        gdf = raster2gpd(InRaster,feature_name)
        
        # Spatial merge on GADM to obtain admin areas
        gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
        
        # Set run fields: datetime, run_id, model
        # first convert dekad of year to day of year
        # note: dekad is a 10 day period so dekad 25 ends the 250th day of the year
        # since dekad 01 contains days 1 through 10 so dekad 01 should yield Jan 1 
        gdf['datetime'] = datetime(self.year, 1, 1) + timedelta((int(self.dekad) * 10) - 11)
        gdf['run_id'] = self.run_id
        gdf['model'] = self.name
        gdf['feature_description'] = feature_description
        del(gdf['geometry'])
        del(gdf['index_right'])

        # perform bulk insert of entire geopandas DF
        logging.info("Storing point data output...")
        db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
        db_session.commit()