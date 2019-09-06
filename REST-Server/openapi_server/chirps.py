import requests
import logging
import boto3
import os

class CHIRPSController(object):
    """
    A controller to manage CHIRPS model execution.
    """

    def __init__(self, model_config, output_path):
        self.model_config = model_config
        self.output_path = output_path
        self.bucket = "world-modelers"
        self.dekad = self.model_config["dekad"]
        self.year = self.model_config["year"]
        self._type = self.model_config["_type"]
        self.url = f"http://chg-ewxtest.chg.ucsb.edu/proxies/wcsProxy.php?layerNameToUse=chirps:"\
                   f"chirps_africa_1-dekad-{self.dekad}-{self.year}_{self._type}"\
                   f"&lowerLeftXToUse=3673536.4017755133&lowerLeftYToUse=378978.68273536063&upperRightXToUse=5341797.050557815"\
                   f"&upperRightYToUse=1676937.5016708253&wcsURLToUse=http://chg-ewxtest.chg.ucsb.edu:8080/geoserver/wcs?&resolution"\
                   f"=0.05&srsToUse=EPSG:3857&outputSrsToUse=EPSG:4326"
        self.result_name = self.model_config['run_id']
        self.key = f"results/chirps/{self.result_name}.tiff"
        self.result_path = output_path


    def run_model(self):
        """
        Obtain CHIRPS data
        """
        data = requests.get(self.url)
        with open(f"{self.output_path}/{self.result_name}.tiff", "wb") as f:
            f.write(data.content)
        self.storeResults()
        return 'SUCCESS'

    
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