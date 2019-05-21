from rasterio.transform import Affine
from rasterio.mask import mask as rast_mask
from rasterio import io as rast_io
import rasterio
import numpy as np
import pandas as pd
import datetime
from ftplib import FTP
import os
import wget
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import zipfile
from rasterio.warp import Resampling, calculate_default_transform, reproject
import fiona
import pyspatialml


def ProjectionFromConfig():
    ncols, nrows = (1416, 1051)
    profile = {
        "driver": "GTiff",
        "height": nrows,
        "width": ncols,
        "count": 1,
        "dtype": np.float32,
        "crs": 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,\
            AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],\
            UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]GEOGCS["WGS 84",\
            DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],\
            AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],\
            AUTHORITY["EPSG","4326"]]GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,\
            298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],\
            UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]]',
        "transform": Affine.from_gdal(
        24.150733709000065,
        0.008334173612994345,
        0,
        12.23635188000003,
        0,
        -0.008331170202664108,
    ),
        "nodata": -9999.0,
    }

    return profile

def ScrapeDailyRainfallData():
    start_date = datetime.date(2017, 8, 15)
    end_date = datetime.date(2017, 8, 30)

    datadir = "./products/ScrapeDailyRainfallData/"
    os.makedirs(datadir, exist_ok=True)

    # connect to FTP
    ftp = FTP("ftp.chg.ucsb.edu")  # noqa: S321 - ignore secuirty check
    ftp.sendcmd("USER anonymous")
    ftp.sendcmd("PASS anonymous@")

    # Date for the data to be downloaded
    delta = end_date - start_date
    dates = [
        start_date + datetime.timedelta(i)
        for i in range(0, delta.days + 1)
    ]
    dates_str = [i.strftime("%Y.%m.%d") for i in dates]
    # Download data
    for year in range(
        start_date.year, end_date.year + 1
    ):
        ftp.cwd(
            f"pub/org/chg/products/CHIRPS-2.0/africa_daily/tifs/p05/{year}/"
        )

        files = ftp.nlst()
        files = [i for i in files if any(d in i for d in dates_str)]
        # Remove folders from the list
        download = [f for f in files if f.endswith(".gz")]

        for f in download:
            if not os.path.isfile(os.path.join(datadir, f.replace(".gz", ""))):
                ftp.retrbinary(
                    "RETR " + f, open(os.path.join(datadir, f), "wb").write
                )
        ftp.cwd("/")
    os.system(f"gunzip {datadir}/*.gz")  # noqa: S605 - ignore secuirty check
    return datadir


def PullTrainDataFromCKAN():
    boundary_url = {"key":"train_data", "url":"https://data.kimetrica.com/dataset/5a778a98-8ef4-4d69-97b8-d87682e00728/resource/bde01941-1980-45a4-b83c-7e865b25baf5/download/sm_train_data.csv"}
    train_data_path = "./products/train_data/"
    file_path = train_data_path + "sm_train_data.csv"
    os.makedirs(train_data_path, exist_ok=True)
    wget.download(boundary_url["url"],train_data_path)
    return file_path

def PullShapefileFilesFromCkan():
    boundary_url = {"key":"boundary", "url":"https://data.kimetrica.com/dataset/2c6b5b5a-97ea-4bd2-9f4b-25919463f62a/resource/4ca5e4e8-2f80-44c4-aac4-379116ffd1d9/download/ss_admin0.zip"}
    shapefile_datadir = "./products/shape_files/"
    os.makedirs(shapefile_datadir, exist_ok=True)
    wget.download(boundary_url["url"],shapefile_datadir)
    return shapefile_datadir

def RasterFiles():
    twi_url = {"key":"twi", "url":"https://data.kimetrica.com/dataset/081a3cca-c6a7-4453-b93c-30ec1c2aec37/resource/30a35367-29f4-4302-901b-02b91d80c4ea/download/twi.tif"}
    landforms_url = {"key":"landforms","url":"https://data.kimetrica.com/dataset/081a3cca-c6a7-4453-b93c-30ec1c2aec37/resource/2bcdd6af-f239-4093-b816-1880da462840/download/landforms.tif"}
    texture_url = {"key":"texture", "url":"https://data.kimetrica.com/dataset/081a3cca-c6a7-4453-b93c-30ec1c2aec37/resource/23c342a0-21da-4706-aef8-32a517a6d7fe/download/texture.tif"}

    raster_datadir = "./products/rasters/"
    os.makedirs(raster_datadir, exist_ok=True)
    for url in [twi_url,landforms_url,texture_url]:
        wget.download(url["url"],raster_datadir)
    return raster_datadir

def TrainSMFromChirpsModel(train_data_path):
    hydrology_test_size = 0.33
    hydrology_ind_vars = [
            "landforms",
            "texture",
            "twi",
            "rain_lag10",
            "rain_lag9",
            "rain_lag8",
            "rain_lag7",
            "rain_lag6",
            "rain_lag5",
            "rain_lag4",
            "rain_lag3",
            "rain_lag2",
            "rain_lag1",
        ]
    hydrology_dep_var = "soil_moisture"

    calculate_influence = False

    COL_INFLUENCE_PERCENT = "influence_percent"
    COL_SOURCE_VARIABLE = "source_variable"


    df = pd.read_csv(train_data_path)
    X, y = df[list(hydrology_ind_vars)], df[hydrology_dep_var]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=hydrology_test_size, random_state=None
    )

    ETR = ExtraTreesRegressor(
            max_depth=200,
            max_features="auto",
            max_leaf_nodes=None,
            min_impurity_decrease=0.0,
            min_samples_leaf=1,
            min_samples_split=5,
            n_estimators=500,
            n_jobs=-1,
        )

    model = Pipeline([("scaling", StandardScaler()), ("regression", ETR)])

    model.fit(X_train, y_train)

    # Calculate the influence grid if needed
    if calculate_influence is True:
        model_importance = model.named_steps["regression"].feature_importances_
        influence_grid = pd.DataFrame(
            [model_importance, hydrology_ind_vars],
            index=["influence_percent", "source_variable"],
            columns=np.arange(0, len(model_importance)),
        ).T

        influenced_variable_name, influence_grid = (hydrology_dep_var, influence_grid)

    return model

def map_f_path(path):
    maps = {os.path.splitext(i)[0]: os.path.join(path, i) for i in os.listdir(path)}
    return maps


def reproject_like(
    rast_file, proj_file, output_file, mode=Resampling.bilinear, nodata=None
):
    """Match the projection and resolution of a raster to another

    Parameters:
        rast_file (str): The file location of the raster to be reprojected
        proj_file (str): The file location of raster to get profile from or raster meta
        output_file (str): The file location of the output raster
        mode (Resampling): The resampling technique

    Returns:
        None
    """
    if isinstance(proj_file, dict):
        kwargs = proj_file
    else:
        with rasterio.open(proj_file) as proj_src:
            kwargs = proj_src.meta.copy()

    if nodata:
        kwargs.update({"nodata": nodata})

    with rasterio.open(rast_file) as src:
        with rasterio.open(output_file, "w", **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=dst.transform,
                dst_crs=dst.crs,
                dst_nodata=dst.nodata,
                resampling=mode,
            )


def inundation_extent(src_file, dst_file, threshold=0.4):
    """Identify areas that are flooded

    Parameters:
        src_file (str): The file path for soil moisture
        dst_file (str): The file path inundation extent
        threshold (float): The threshold for identifying inudation

    Returns:
        None
    """
    with rasterio.open(src_file) as src:
        arr = np.squeeze(src.read(1))
        nodata = src.nodata
        meta = src.meta.copy()

    mask = arr == nodata
    arr = np.where(arr >= threshold, 1, 0)
    arr[mask] = nodata

    with rasterio.open(dst_file, "w", **meta) as dst:
        dst.write(np.float32(arr), 1)


def extract_zipfile(zipath, filename, path):
    """ Un zip zipped file and one file

    Parameters:
        zippath (str): zipped file path
        filename (str): file name to be extrctaed

    Returns:
        str: The location of the file
    """
    zip_ref = zipfile.ZipFile(zipath, "r")
    zip_ref.extractall(path=path)
    fp = zip_ref.extract(filename, path=path)
    zip_ref.close()
    return fp

def mask_raster(src_name, dst_name, features, no_data_val=-9999.0, date=None):
    """ Mask raster using shapefile

        Parameters:
            src_name (str): The file location of the raster to be masked
            dst_name (str): The file location of the output raster
            features (): The fatures to be used to mask raster
            no_data_val (float): The value rep missing values

        Returns:
            None
        """
    if isinstance(features, str):
        with fiona.open(features, "r") as shp:
            features = [feature["geometry"] for feature in shp]

    if isinstance(src_name, rast_io.DatasetReader):
        out_image, out_transform = rast_mask(
            src_name, features, filled=True, crop=True, nodata=no_data_val
        )
        out_meta = src_name.meta.copy()
    else:
        with rasterio.open(src_name) as src:
            out_image, out_transform = rast_mask(
                src, features, filled=True, crop=True, nodata=no_data_val
            )
        out_meta = src.meta.copy()

    out_meta.update(
        {
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": no_data_val,
            "dtype": "float32",
        }
    )
    with rasterio.open(dst_name, "w", **out_meta) as dst:
        dst.write(np.float32(out_image))
        if date:
            dst.update_tags(Time=date)



def ClipDailyRainfallData(rainfall_datadir,shapefile_datadir):
    data_dir = "./products/ClipDailyRainfallData/"
    data_map = map_f_path(rainfall_datadir)
    shapefile = extract_zipfile(shapefile_datadir + "ss_admin0.zip", "ss_admin0.shp", shapefile_datadir)

    os.makedirs(data_dir, exist_ok=True)

    for key, src_name in data_map.items():
        i = key.replace("chirps-v2.0.", "")
        i = i.replace(".", "")
        dst_name = os.path.join(data_dir, f"{i}.tif")
        mask_raster(src_name, dst_name, shapefile)
    return data_dir



def RainFallSimulation(model, config, resampled_dir, clipdaily_datadir):

    """
    Impact of rainfall on soil moisture and inundation extent
    """

    date = datetime.datetime(2017, 8, 28)
    PercentOfNormalRainfall = 1.0
    num_days = 10


    chirp_map = map_f_path(clipdaily_datadir)
    raster_map = map_f_path(resampled_dir)

    ref_proj = config

    files = sorted(
        (date - datetime.timedelta(days=i + 1)).strftime("%Y%m%d")
        for i in range(num_days)
    )

    output_dir = "./output/hydrology_model"

    # Simulate rainfall data
    for key in files:
        with rasterio.open(chirp_map[key]) as src:
            arr = np.squeeze(src.read(1))
            nodata = src.nodata
            mask = arr == nodata
            arr = arr * PercentOfNormalRainfall
            arr[mask] = nodata
            meta = src.meta.copy()
            dst_name = os.path.join(
                output_dir, f"{key}.tif"
            )
            os.makedirs(output_dir, exist_ok=True)
            with rasterio.open(dst_name, "w", **meta) as dst:
                dst.write(arr, 1)

    # Predict soil moisture
    c_vars = sorted(raster_map[key] for key in raster_map)
    chirps = [
        os.path.join(output_dir, f"{key}.tif")
        for key in files
    ]
    features = c_vars + chirps

    # Stack Features
    stack = pyspatialml.stack_from_files(features)

    sm_path = output_dir + "/soil_moisture.tif"

    # Predict the soil moisture
    stack.predict(estimator=model, file_path=sm_path, nodata=-9999.0)

    # Inundation extent
    extent_file = output_dir + "/inundation.tif"
    inundation_extent(sm_path, extent_file)

    # Resample Inundation extent to 1km resolution
    reproject_like(
        rast_file=extent_file,
        proj_file=ref_proj,
        output_file=extent_file,
        mode=Resampling.nearest,
    )

    # Resample soil moisture to 1km
    reproject_like(rast_file=sm_path, proj_file=ref_proj, output_file=sm_path)


def ResampleRastersToMatchChirps(ndvi_input,SPL3SMP_input):
    if type(ndvi_input) == dict:
        try:
            ndvi__dict = {k: v.path for k, v in ndvi_input.items()}
        except AttributeError:
            ndvi__dict = ndvi_input
    else:
        ndvi__dict = map_f_path(ndvi_input)

    if isinstance(SPL3SMP_input, dict):
        try:
            SPL3SMP_file = list(SPL3SMP_input.values())[0].path
        except AttributeError:
            SPL3SMP_file = list(SPL3SMP_input.values())[0]
    else:
        SPL3SMP_map = map_f_path(SPL3SMP_input)
        SPL3SMP_file = list(SPL3SMP_map.values())[0]

    tmpdir = "./products/Resampled/"
    os.makedirs(tmpdir, exist_ok=True)
    for key in ndvi__dict:
        reproject_like(
            rast_file=ndvi__dict[key],
            proj_file=SPL3SMP_file,
            output_file=os.path.join(tmpdir, f"{key}.tif"),
            nodata=-9999.0,
        )
    return tmpdir


# Independent Tasks
config = ProjectionFromConfig()
rainfall_datadir = ScrapeDailyRainfallData()
raster_datadir = RasterFiles()
shapefile_datadir = PullShapefileFilesFromCkan()
train_datadir = PullTrainDataFromCKAN()


model = TrainSMFromChirpsModel(train_datadir)
clipdaily_datadir = ClipDailyRainfallData(rainfall_datadir,shapefile_datadir)
resampled_dir = ResampleRastersToMatchChirps(raster_datadir,clipdaily_datadir)

# Final output task
RainFallSimulation(model, config, resampled_dir, clipdaily_datadir)

