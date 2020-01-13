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

def PIHM_reproject(InRaster, OutRaster):
    dst_crs = 'EPSG:102022'

    with rasterio.open(InRaster) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(OutRaster, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

def raster2gpd(InRaster,feature_name,band=1,nodataval=-9999):
    '''
    Description: 
        Takes the path of a raster (.tiff) file and produces a Geopandas Data Frame.
    Params:
        - InRaster: the path of the input raster file
        - feature_name: the name of the feature represented by the pixel values 
    '''

    with rasterio.open(InRaster) as r:
        T0 = r.transform  # upper-left pixel corner affine transform
        p1 = Proj(r.crs)

    p2 = Proj(proj='latlong',datum='WGS84')


    # open the raster and get some properties
    ds       = gdal.OpenShared(InRaster,gdalconst.GA_ReadOnly)
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

                points.append([X,Y,RowData[ThisCol],feature_name])

    gdf = gpd.GeoDataFrame(points, columns=['longitude','latitude','feature_value','feature_name'])
    X, Y = list(gdf.longitude), list(gdf.latitude)
    T = transform(p1, p2, X, Y)
    gdf['latitude'] = T[1]
    gdf['longitude'] = T[0]
    gdf['geometry'] = gdf.apply(lambda x: Point(x.longitude, x.latitude),axis=1)
    return gdf

def ingest_to_db(InRaster, run_id, *,
                model_name, start, included_months, total_months,
                params, basin):

    # Add metadata object to DB
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    raw_output_link= f"https://model-service.worldmodelers.com/results/PIHM_results/{run_id}.tif",
                    run_label=f"{model_name} run for {basin} Basin.",
                    point_resolution_meters=200)
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    print("Storing parameters...")
    for pp, vv in params.items():

        if pp == 'basin':
            p_type = 'string'
        else:
            p_type = 'float'
            
        param = Parameters(run_id=run_id,
                          model=model_name,
                          parameter_name=pp,
                          parameter_value=vv,
                          parameter_type=p_type
                          )
        db_session.add(param)
        db_session.commit()        
        
    # iterate over the bands that should be included (1 per month)
    for month in range(1, included_months + 2):
        date_ = start + relativedelta(months=month-1)
        date_str = date_.strftime("%m/%d/%Y")        
        print(f"Processing {model_name} {date_str}")
        # Convert Raster to GeoPandas
        feature_name = m['outputs'][0]['name']
        feature_description = m['outputs'][0]['description']
        gdf = raster2gpd(InRaster,feature_name,band=month)

        print(f"Performing spatial merge")
        # Spatial merge on GADM to obtain admin areas
        gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
        
        # Iterate over years for each band to ensure that there is continous
        # annual data
        # Set run fields: datetime, run_id, model
        gdf['datetime'] = date_
        gdf['run_id'] = run_id
        gdf['model'] = model_name
        gdf['feature_description'] = feature_description
        if 'geometry' in gdf:
            del(gdf['geometry'])
            del(gdf['index_right'])

        # perform bulk insert of entire geopandas DF
        print(f"Ingesting {date_str} of {model_name} for basin {basin} to database\n")
        db_session.bulk_insert_mappings(Output, gdf.to_dict(orient="records"))
        db_session.commit()    

def gen_run(input_file, *, model_name, precipitation, temperature, evapotranspiration, basin):
    model_config = {
                    'config': {
                        "precipitation": precipitation,
                        "temperature": temperature,
                        "evapotranspiration": evapotranspiration,
                        "basin": basin
                    },
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

def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def included_months(end):
    d_start = datetime(year=end.year - 10, month=1,day=1)
    return diff_month(end,d_start)

def included_start(end):
    return datetime(year=end.year - 10, month=1,day=1)    

def main(meta_df, tmp_output):
    for kk, vv in meta_df.iterrows():
        url = vv['pihm-output']
        start = vv['start']
        end = vv['end']
        included_months = vv['included_months']
        included_start = vv['included_start']
        total_months = vv['total_months']
        basin = vv['basin']
        params = {'precipitation': vv['precipitation'], 
                  'temperature': vv['temperature'],
                  'evapotranspiration': vv['evapotranspiration'],
                  'basin': vv['basin']}

        if not check_run_in_redis(model_name,params):

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
            
            InRaster = list(glob.iglob(f'{tmp_output}-output/output/output/**/vis/Flood_surf.tif', recursive=True))[0]
            print(f"Using initial raster {InRaster}")

            run_id, model_config = gen_run(InRaster, 
                                           model_name=model_name, 
                                           precipitation=vv.precipitation, 
                                           temperature=vv.temperature,
                                           evapotranspiration=vv.evapotranspiration,
                                           basin=vv.basin)
            
            ReProjRaster = "reprojected.tif"
            PIHM_reproject(InRaster, ReProjRaster)
            ingest_to_db(ReProjRaster, run_id, model_name=model_name, 
                         start=included_start, included_months=included_months, 
                         total_months=total_months, params=params, basin=basin)    

        else:
            print(f"Run with params {json.dumps(params)} already in MaaS.")

if __name__ == "__main__":
    init_db()

    # Load Admin2 shape from GADM
    print("Loading GADM shapes...")
    admin2 = gpd.read_file(f"{config['GADM']['GADM_PATH']}/gadm36_2.shp")
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]   

    with open('../metadata/models/PIHM-model-metadata.yaml', 'r') as stream:
        m = yaml.safe_load(stream)
    
    model_name = m['id']    

    parameters =  {"TS_PRCP":"precipitation",
                   "TS_SFCTMP": "temperature",
                   "ET_ETP": "evapotranspiration",
                   "basin": "basin"}

    meta_files = glob.iglob('PIHM-Meta-Files/pihm-v4*.csv')
    
    for f in meta_files:
        print(f"Processing {f}")
        meta_df = pd.read_csv(f)
        meta_df['end'] = meta_df['end-date'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
        meta_df['start'] = meta_df['start-date'].apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
        meta_df['total_months'] = meta_df.apply(lambda x: diff_month(x.end, x.start), axis=1)
        meta_df['included_months'] = meta_df.apply(lambda x: included_months(x.end), axis=1)    
        meta_df['included_start'] = meta_df['end'].apply(lambda x: included_start(x))
        meta_df['basin'] = f.split('_')[1].split('.csv')[0]

        print(meta_df[['start','end','total_months','included_months','basin']].head())

        # rename columns to human readable labels for temp/precip
        for kk, vv in parameters.items():
            meta_df[vv] = meta_df[kk]
            
        tmp_output = 'pihm-tmp'

        main(meta_df, tmp_output)