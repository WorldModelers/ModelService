import sys
import warnings
sys.path.append("../db")

if not sys.warnoptions:
    warnings.simplefilter("ignore")

from database import init_db, db_session
from models import Metadata, Output, Parameters

import geopandas as gpd
from shapely.geometry import Point

import netCDF4
from netCDF4 import Dataset
import datetime
import pandas as pd
import numpy as np
import json
import csv
from collections import OrderedDict
from hashlib import sha256

features = {'days_medium': 'Number of days in the month with medium flooding (2-yr flood)',
            'days_high': 'Number of days in the month with high flooding (5-yr flood)',
            'days_severe': 'Number of days in the month with severe flooding (20-yr flood)'
           }

def days_medium(f):
    if f==1:
        return 1
    else:
        return 0
    
def days_high(f):
    if f==2:
        return 1
    else:
        return 0
    
def days_severe(f):
    if f==3:
        return 1
    else:
        return 0 
    
def convert_to_int(x):
    try:
        return int(float(x))
    except:
        return np.nan    

def gen_run_id(year):
    model_name = 'flood_index_model'
    model_config = {
                    'config': {
                        "year": year
                    },
                    'name': model_name
                   }

    model_config = sortOD(OrderedDict(model_config))

    run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()
    return run_id

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res    

def ingest2db(year, df, filename):
    model_name = "flood_index_model"
    init_db()

    # Load Admin2 shape from GADM
    logging.info("Loading GADM shapes...")
    admin2 = gpd.read_file("../gadm2/gadm36_2.shp")
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]

    # Add metadata object to DB
    # TODO: add run_label and run_description
    logging.info("Storing metadata...")
    meta = Metadata(run_id=gen_run_id(year), 
                    model=model_name,
                    run_description=f"{model_name} run for {year}",
                    raw_output_link= f'https://s3.amazonaws.com/world-modelers/flood_index_model/{filename}',
                    # 0.1 degrees (~10km)
                    point_resolution_meters=10000) 
    logging.info("Storing metadata...")
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    logging.info("Storing parameters...")
    param = Parameters(run_id=run_id,
                      model=model_name,
                      parameter_name="year",
                      parameter_value=year,
                      parameter_type="the modeled year"
                      )
    db_session.add(param)
    db_session.commit()

    # Process CSV and normalize it
    logging.info("Processing points...")

    df['geometry'] = df.apply(lambda x: Point(x.longitude, x.latitude), axis=1)
    df['run_id'] = run_id
    df['model'] = model_name

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
    for feature_name, feature_description in features.items():
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