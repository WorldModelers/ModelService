import requests
import logging
import boto3
import os
from pyproj import Proj, transform
import configparser
import redis


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

        # The Redis connection has to be instantiated by this Class
        # since once instantiated, it cannot be pickled by RQ
        self.r = redis.Redis(host=config['REDIS']['HOST'],
                        port=config['REDIS']['PORT'],
                        db=config['REDIS']['DB'])          


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