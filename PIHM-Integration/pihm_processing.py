import boto3
import os
import shutil
import configparser
import redis
import yaml

import sys
import os
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

from shapely.geometry import Point
import geopandas as gpd
import pandas as pd
import numpy as np
from osgeo import gdal
from osgeo import gdalconst
import tarfile

from datetime import datetime
from hashlib import sha256
from collections import OrderedDict
import json
import urllib.request

config = configparser.ConfigParser()
config.read('../REST-Server/config.ini')

r = redis.Redis(host=config['REDIS']['HOST'],
                port=config['REDIS']['PORT'],
                db=config['REDIS']['DB'])

profile = "wmuser"
bucket = "world-modelers"

session = boto3.Session(profile_name=profile)
s3 = session.resource("s3")
s3_client = session.client("s3")
s3_bucket= s3.Bucket(bucket)

def raster2gpd(InRaster,feature_name,band=1,nodataval=-9999):
    '''
    Description: 
        Takes the path of a raster (.tiff) file and produces a Geopandas Data Frame.
    Params:
        - InRaster: the path of the input raster file
        - feature_name: the name of the feature represented by the pixel values 
    '''

    # open the raster and get some properties
    ds       = gdal.OpenShared(InRaster,gdalconst.GA_ReadOnly)
    ds       = gdal.Warp('out_raster.tif', ds, dstSRS='EPSG:4326') # fixes projection issue
    GeoTrans = ds.GetGeoTransform()
    ColRange = range(ds.RasterXSize)
    RowRange = range(ds.RasterYSize)
    rBand    = ds.GetRasterBand(band) # first band
    nData    = np.float32(rBand.GetNoDataValue())
    if nData == None:
        print("No nodataval for raster")
        nData = nodataval # set it to something if not set
    else:
        print("NoData value is {0}".format(nData))

    # specify the center offset (takes the point in middle of pixel)
    HalfX    = GeoTrans[1] / 2
    HalfY    = GeoTrans[5] / 2

    points = []
    for ThisRow in RowRange:
        RowData = rBand.ReadAsArray(0,ThisRow,ds.RasterXSize,1)[0]
        for ThisCol in ColRange:
            # need to exclude NaN values since there is no nodataval
            if (np.float32(RowData[ThisCol]) != nData) and not (np.isnan(RowData[ThisCol])):
                
                # TODO: implement filters on valid pixels
                # for example, the below would ensure pixel values are between -100 and 100
                #if (RowData[ThisCol] <= 100) and (RowData[ThisCol] >= -100):

                X = GeoTrans[0] + ( ThisCol * GeoTrans[1] )
                Y = GeoTrans[3] + ( ThisRow * GeoTrans[5] ) # Y is negative so it's a minus
                # this gives the upper left of the cell, offset by half a cell to get centre
                X += HalfX
                Y += HalfY

                points.append([Point(X, Y),X,Y,RowData[ThisCol],feature_name])

    return gpd.GeoDataFrame(points, columns=['geometry','longitude','latitude','feature_value','feature_name'])

def ingest_to_db(InRaster, run_id, model_name, year):

        # Add metadata object to DB
        meta = Metadata(run_id=run_id, 
                        model=model_name,
                        raw_output_link= f"https://model-service.worldmodelers.com/results/PIHM_results/{run_id}.tif",
                        run_label=model_name,
                        point_resolution_meters=2000)
        db_session.add(meta)
        db_session.commit()
            
        # iterate over the 12 bands (1 per month)
        for month in range(1,13):
            print(f"Processing {model_name} {month}")
            # Convert Raster to GeoPandas
            feature_name = m['outputs'][0]['name']
            feature_description = m['outputs'][0]['description']
            gdf = raster2gpd(InRaster,feature_name,band=month)

            print(f"Performing spatial merge")
            # Spatial merge on GADM to obtain admin areas
            gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
            
            # Iterate over years for each band to ensure that there is continous
            # annual data
            for year in years:
                # Set run fields: datetime, run_id, model
                gdf['datetime'] = datetime(year=year, month=month, day=1)
                gdf['run_id'] = run_id
                gdf['model'] = model_config['name']
                gdf['feature_description'] = feature_description
                if 'geometry' in gdf:
                    del(gdf['geometry'])
                    del(gdf['index_right'])

                # perform bulk insert of entire geopandas DF
                print(f"Ingesting {year} of {model_name} to database\n")
                db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
                db_session.commit()    

def gen_run(input_file, model_name=None, precipitation=None, temperature=None):
    model_config = {
                    'config': {
                        "precipitation": precipitation,
                        "temperature": temperature
                    },
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    print(dict(model_config))
    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/{model_name}_results/{run_id}.tif"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
    # Upload file to S3
    print(f"Uploading {run_obj['key']}...")
    s3_bucket.upload_file(input_file, run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config
          
def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res                              

if __name__ == "__main__":
    init_db()

    # Load Admin2 shape from GADM
    logging.info("Loading GADM shapes...")
    admin2 = gpd.read_file(f'{self.gadm}/gadm36_2.shp')
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]    

    with open('../metadata/models/PIHM-model-metadata.yaml', 'r') as stream:
        m = yaml.safe_load(stream)
    
    model_name = m['id']    

    # Wipe runs for the model
    r.delete(model_name)

    parameters =  {"TS_PRCP":"precipitation",
                   "TS_SFCTMP": "temperature"}

    meta_df = pd.read_csv('pihm-v4.1.0.csv')

    # rename columns to human readable labels for temp/precip
    for kk, vv in parameters.items():
        meta_df[vv] = meta_df[kk]
        
    tmp_output = 'pihm-tmp'
    
    # loop over model runs
    for kk, vv in meta_df.iterrows():
        url = vv['pihm-output']
        year = int(vv['end-date'].split('/')[-1])

        print(f"Downloading from {url}...")
        
        if os.path.exists(f"{tmp_output}.tar.gz"):
            os.remove(f"{tmp_output}.tar.gz")
        if os.path.exists(f"{tmp_output}-output"):
            shutil.rmtree(f"{tmp_output}-output")        
        
        # download file to `pihm-tmp.tar.gz`
        urllib.request.urlretrieve(url, f"{tmp_output}.tar.gz") 
        
        # unzip tarball to `pihm-tmp-output`
        tar = tarfile.open(f"{tmp_output}.tar.gz", "r:gz")
        tar.extractall(path=f"{tmp_output}-output")
        tar.close()
        
        InRaster = f"{tmp_output}-output/output/output/muger.out/vis/Flood_surf.tif"

        run_id, model_config = gen_run(InRaster, model_name=model_name, precipitation=vv.precipitation, temperature=vv.temperature)
        
        ingest_to_db(InRaster, run_id, model_name, year)    