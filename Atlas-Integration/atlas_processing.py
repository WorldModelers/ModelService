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
import numpy as np
from osgeo import gdal
from osgeo import gdalconst

from datetime import datetime
from hashlib import sha256
from collections import OrderedDict
import json

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
    nData    = rBand.GetNoDataValue()
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
            if (RowData[ThisCol] != nData) and not (np.isnan(RowData[ThisCol])):
                
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


if __name__ == "__main__":

    init_db()

    # Load Admin2 shape from GADM
    print("Loading GADM shapes...")
    admin2 = gpd.read_file('../gadm2/gadm36_2.shp')
    admin2['country'] = admin2['NAME_0']
    admin2['state'] = admin2['NAME_1']
    admin2['admin1'] = admin2['NAME_1']
    admin2['admin2'] = admin2['NAME_2']
    admin2 = admin2[['geometry','country','state','admin1','admin2']]
    print("...loaded\n")

    models = ['consumption_model','asset_wealth_model']
    formats = ['tif','geojson']
    atlas_lookup = {
                   'asset_wealth_model':{
                      'geojson':'november_tests_asset_wealth.geojson',
                      'tif':'november_tests_atlasai_assetwealth_allyears_2km.tif',
                      'feature_name': 'poverty level',
                      'feature_description':'Measure of household poverty levels based on the assets they own (unitless)'
                   },
                   'consumption_model':{
                      'geojson':'november_tests_consumption.geojson',
                      'tif':'november_tests_atlasai_consumption_allyears_2km.tif',
                      'feature_name': 'consumption per capita per day',
                      'feature_description':'Measure of how much a person would spend each day (2011 USD per capita per day)'
                   }
                }

    bands = {1:[2018,2017,2016,2015], 
             2:[2014,2013,2012,2011],
             3:[2010,2009,2008,2007],
             4:[2006,2005,2004,2003]}

    for model_name in models:

        model_config = {
          "config": {"format": 'tif'},
          "name": model_name
        }
        
        run_id = sha256(json.dumps(model_config).encode('utf-8')).hexdigest()

        # Add metadata object to DB
        meta = Metadata(run_id=run_id, 
                        model=model_name,
                        raw_output_link= f"https://model-service.worldmodelers.com/result_file/{run_id}.tif",
                        run_label=model_name.replace('_', ' ').title(),
                        point_resolution_meters=2000)
        db_session.add(meta)
        db_session.commit()
            
        # iterate over the 4 bands
        for band, years in bands.items():
            print(f"Processing {model_name} band {band}")
            # Convert Raster to GeoPandas
            InRaster = f"data/{atlas_lookup[model_name]['tif']}"
            feature_name = atlas_lookup[model_name]['feature_name']
            feature_description = atlas_lookup[model_name]['feature_description']
            gdf = raster2gpd(InRaster,feature_name,band=band)

            print(f"Performing spatial merge")
            # Spatial merge on GADM to obtain admin areas
            gdf = gpd.sjoin(gdf, admin2, how="left", op='intersects')
            
            # Iterate over years for each band to ensure that there is continous
            # annual data
            for year in years:
                # Set run fields: datetime, run_id, model
                gdf['datetime'] = datetime(year=year, month=1, day=1)
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