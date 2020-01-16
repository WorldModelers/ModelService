import boto3
import os
import shutil
import configparser
import logging
import redis
import yaml
import glob

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
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import Proj, transform
import pandas as pd
import numpy as np
from osgeo import gdal
from osgeo import gdalconst
import tarfile

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
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


bands = {
        "Meat": 1,
        "Pulses and vegetables": 2,
        "Bread and Cereals": 3, 
        "Milk, cheese and eggs": 4,
        "Sugar, jam, honey, chocolate and candy": 5,
        "Oils and fats": 6
    }


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
    GeoTrans = ds.GetGeoTransform()
    ColRange = range(ds.RasterXSize)
    RowRange = range(ds.RasterYSize)
    rBand    = ds.GetRasterBand(band) # first band
    nData    = rBand.GetNoDataValue()
    if nData == None:
        logging.info(f"No nodataval found, setting to {nodataval}")
        nData = np.float64(nodataval) # set it to something if not set
    else:
        nData = np.float64(nodataval)
        logging.info(f"Nodataval is: {nData}")

    # specify the center offset (takes the point in middle of pixel)
    HalfX    = GeoTrans[1] / 2
    HalfY    = GeoTrans[5] / 2

    # Check that NoDataValue is of the same type as the raster data
    RowData = rBand.ReadAsArray(0,0,ds.RasterXSize,1)[0]
    if type(nData) != type(RowData[0]):
        logging.warning(f"NoData type mismatch: NoDataValue is type {type(nData)} and raster data is type {type(RowData[0])}")
        

    points = []
    for ThisRow in RowRange:
        RowData = rBand.ReadAsArray(0,ThisRow,ds.RasterXSize,1)[0]
        for ThisCol in ColRange:
            # need to exclude NaN values since there is no nodataval
            if (RowData[ThisCol] != nData) and not (np.isnan(RowData[ThisCol])):
                
                # TODO: implement filters on valid pixels
                # for example, the below would ensure pixel values are between -100 and 100
                #if (RowData[ThisCol] <= 100) and (RowData[ThisCol] >= -100):

                X = GeoTrans[0] + ( ThisCol * GeoTrans[1] )
                Y = GeoTrans[3] + ( ThisRow * GeoTrans[5] ) # Y is negative so it's a minus
                # this gives the upper left of the cell, offset by half a cell to get centre
                X += HalfX
                Y += HalfY

                # ROUND LAT/LON to 1 DECIMAL DEGREE
                points.append([Point(round(X,1), round(Y,1)),round(X,1),round(Y,1),RowData[ThisCol],feature_name])

    return gpd.GeoDataFrame(points, columns=['geometry','longitude','latitude','feature_value','feature_name'])

def ingest_to_db(InRaster, run_id, *,
                model_name, params, m):

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/{model_name}_results/{run_id}.tif",
                    run_label=f"{model_name} run.",
                    point_resolution_meters=1000000)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    print("Storing parameters...")
    for pp, vv in params.items():
        if pp == 'year' or pp=='month':
            p_type = 'integer'
        else:
            p_type = 'string'
            
        param = Parameters(run_id=run_id,
                          model=model_name,
                          parameter_name=pp,
                          parameter_value=vv,
                          parameter_type=p_type
                          )
        db_session.add(param)
        db_session.commit()       
      
    band = bands[params['commodity']]
    # Convert Raster to GeoPandas
    feature_name = m['outputs'][0]['name']
    feature_description = m['outputs'][0]['description']
    gdf = raster2gpd(InRaster,feature_name,band=band)

    print(f"GDF size is {gdf.shape[0]} before rounding lat/lon")
    gdf = gdf.drop_duplicates()
    print(f"GDF size is {gdf.shape[0]} after rounding lat/lon")

    print(f"Performing spatial merge")
    # Spatial merge on GADM to obtain admin areas
    gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
    
    # Iterate over years for each band to ensure that there is continous
    # annual data
    # Set run fields: datetime, run_id, model
    gdf['datetime'] = datetime(year=params['year'], month=params['month'], day=1)
    gdf['run_id'] = run_id
    gdf['model'] = model_name
    gdf['feature_description'] = feature_description
    if 'geometry' in gdf:
        del(gdf['geometry'])
        del(gdf['index_right'])

    # perform bulk insert of entire geopandas DF
    db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
    db_session.commit()    

def gen_run(model_name, params):
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    print(run_id)
    # Add to model set in Redis
    r.sadd(model_name, run_id)
    
    run_obj = {'status': 'SUCCESS',
     'name': model_name,
     'config': model_config["config"],
     'bucket': bucket,
     'key': f"results/{model_name}_results/{run_id}.tiff"
    }

    run_obj['config']['run_id'] = run_id
    run_obj['config'] = json.dumps(run_obj['config'])
    
    # Upload file to S3
    print(f"Uploading {run_obj['key']}...")
    # s3_bucket.upload_file(f, run_obj['key'], ExtraArgs={'ACL':'public-read'})

    # Create Redis object
    r.hmset(run_id, run_obj)
    
    return run_id, model_config

def check_run_in_redis(model_name, params):
    """Returns TRUE if run is already in Redis"""
    model_config = {
                    'config': params,
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))
    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    checked = r.sismember(model_name, run_id)
    if checked:
        print(f"run_id {run_id} found in Redis")
    else:
        print(f"run_id {run_id} NOT found in Redis")

    # Check if run in Redis
    return r.sismember(model_name, run_id)

          
def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res

def main(f, *, model_name, params, m):
    ingest_to_db(f, run_id, model_name=model_name, params=params, m=m)    

if __name__ == "__main__":
    init_db()

    # # download DSSAT files
    print("Downloading market price data files...")
    urllib.request.urlretrieve("https://world-modelers.s3.amazonaws.com/data/Kimetrica/market-price-data.zip", "market-price-data.zip")

    print("Unpacking market price data files...")
    shutil.unpack_archive("market-price-data.zip")    

    # File and folder paths
    files = glob.glob('market-price-data/**/**.tiff')
    print(files)

    # Load Admin2 shape from GADM
    print("Loading GADM shapes...")
    admin2 = gpd.read_file(f"{config['GADM']['GADM_PATH']}/gadm36_2.shp")
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]   

    with open('../metadata/models/market-price-model-metadata.yaml', 'r') as stream:
        m = yaml.safe_load(stream)
    
    model_name = m['id']

    for f in files:
        split = f.split('/')[-1].split('_')
        country = split[0]
        rainfall_scenario = split[4]
        date = split[1]
        year = int(date.split('-')[0])
        month = int(date.split('-')[1])

        for commodity in bands.keys():
            params = {'country': country, 'rainfall_scenario': rainfall_scenario, 'year': year, 'month': month, 'commodity': commodity}
            if not check_run_in_redis(model_name,params):
                print(f"Processing {model_name} for {params['year']}-{params['month']} and {params['commodity']} with rainfall {params['rainfall_scenario']}")
                run_id, model_config = gen_run(model_name, params)
                main(f, model_name=model_name, params=params, m=m)
            else:
                print("Run already in Redis")