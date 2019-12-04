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

file_lookup = {'floodIndex-78318c49e3646c852483accdeb818081':2017
                'floodIndex-1c014ca61fc333d133d2401374073494':2016
                'floodIndex-3961fe71a70139a2b2e5ed6b6d182e15':2015
                'floodIndex-0cfb68f31772caecb01bee5a65b4f045':2014
                'floodIndex-fa3dec98034bcc82a593a13dd0e89b82':2013
                'floodIndex-916386f3d55ab25c7db1f87412f230d4':2012
                'floodIndex-ba82906887e217d8f2b39e0c3f484a4e':2011
                'floodIndex-800d64cd6c045767e8b6df1f0cfc1b7b':2010
                'floodIndex-12284f102e499a616ccd44256c316eb7':2009
                'floodIndex-33d0562575aa85c2c16e176cfc38fe06':2008}

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

def gen_monthly(file_name):
    rootgrp = Dataset(f"flood_results/{file_name}, "r", format="NETCDF4")
    time_var = rootgrp.variables['time']
    days = len(rootgrp.variables['time'])
    lats = len(rootgrp.variables['lat'])
    lons = len(rootgrp.variables['lon'])


    converted_dates = []
    def format_date(day_of_year):
        d = netCDF4.num2date(time_var[day_of_year],time_var.units)
        year = d.year
        month = d.month
        day = d.day
        return datetime.datetime(year=year, month=month, day=day)    

    for day in range(days):
        converted_dates.append(format_date(day))

    cd = np.array(converted_dates)
    time = np.repeat(cd[:, np.newaxis], 120, axis=1)
    time = np.repeat(time[:,:, np.newaxis], 250, axis=2).flatten()
    lat = np.repeat(rootgrp['lat'][:][np.newaxis, :], 365, axis=0)
    lat = np.repeat(lat[:,:,np.newaxis], 250, axis=2).flatten()
    lon = np.repeat(rootgrp['lon'][:][np.newaxis, :], 120, axis = 0)
    lon = np.repeat(lon[np.newaxis, :, :], 365, axis=0).flatten()
    flood = rootgrp['flood'][:].flatten()
    out = np.vstack([time, lat.data, lon.data, flood.data]).transpose()
    
    df = pd.DataFrame(out, columns=['datetime','latitude','longitude','flood-index'])
    df['flood-index'] = df['flood-index'].apply(lambda x: convert_to_int(x))
    df['month'] = df.datetime.apply(lambda x: x.month)
    df['year'] = df.datetime.apply(lambda x: x.year)
    df['days_medium'] = df['flood-index'].apply(lambda x: days_medium(x))
    df['days_high'] = df['flood-index'].apply(lambda x: days_high(x))
    df['days_severe'] = df['flood-index'].apply(lambda x: days_severe(x))    
    
    monthly = pd.DataFrame(df.groupby(['year','month','latitude','longitude'])['days_medium','days_high','days_severe'].sum()).reset_index()
    monthly['datetime'] = monthly.apply(lambda row: datetime.datetime(year=int(row['year']),month=int(row['month']),day=1), axis=1)
    del(monthly['year'])
    del(monthly['month'])
    
    return monthly

def ingest2db(year, df, filename):
    model_name = "flood_index_model"
    run_id = gen_run_id(year)
    init_db()

    # Load Admin2 shape from GADM
    print("Loading GADM shapes...")
    admin2 = gpd.read_file("../gadm2/gadm36_2.shp")
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]

    # Add metadata object to DB
    # TODO: add run_label and run_description
    print("Storing metadata...")
    meta = Metadata(run_id=run_id, 
                    model=model_name,
                    run_description=f"{model_name} run for {year}",
                    raw_output_link= f'https://s3.amazonaws.com/world-modelers/flood_index_model/{filename}.nc',
                    # 0.1 degrees (~10km)
                    point_resolution_meters=10000) 
    print("Storing metadata...")
    db_session.add(meta)
    db_session.commit()

    # Add parameters to DB
    print("Storing parameters...")
    param = Parameters(run_id=run_id,
                      model=model_name,
                      parameter_name="year",
                      parameter_value=year,
                      parameter_type="the modeled year"
                      )
    db_session.add(param)
    db_session.commit()

    # Process CSV and normalize it
    print("Processing points...")

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
        print(f"Storing point data output for {feature_name}...")
        db_session.bulk_insert_mappings(Output, gdf_.to_dict(orient="records"))
        db_session.commit()

if __name__ == "__main__":

    for input_file, year in file_lookup.items():
        monthly = gen_monthly(input_file)
        ingest2db(year, monthly, input_file)                                   