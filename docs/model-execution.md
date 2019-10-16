# Model Execution
Models can be executed using the `/run_model` endpoint. To do this, you must provide a valid JSON configuration. Each model has a unique configuration that can be provided. Below are example configurations for each model.

## Contents

- [Kimetrica Population Model](#kimetrica-population-model)
- [Kimetrica Malnutrition Model](#kimetrica-malnutrition-model)
- [Food Shocks Cascade Model](#food-shocks-cascade-model)
- [DSSAT](#DSSAT)
- [Atlas](#Atlas)
- [CHIRPS and CHIRPS-GEFS](#CHIRPS-and-CHIRPS-GEFS)
- [Yield Anomalies (LPJmL)](#Yield-Anomalies-LPJmL)

### Kimetrica Population Model

```
{
  "config": {},
  "name": "population_model"
}
```

### Kimetrica Malnutrition Model
The percentage of rainfall can be specified for this model by providing a `float` based on the following scale: `0` is no rainfall, `1` is the same as the recorded amount, `2` is 2 times the recorded amount, etc.

```
{
   "config":{
      "percent_of_normal_rainfall":100.0
   },
   "name":"malnutrition_model"
}
```

### Food Shocks Cascade Model
Information about the specific parameters for FSC can be found [here.](https://github.com/WorldModelers/ModelService/blob/master/FSC-Integration/FSC-metadata.yaml#L306-L328)

```
{
   "config":{
      "country":"USA",
      "fractional_reserve_access":0.8,
      "production_decrease":0.2,
      "year":2005
   },
   "name":"FSC"
}
```

### DSSAT
Note that `samples` denotes the number of pixel predictions DSSAT will make. Setting `samples` to `0` returns the entire geography (all Ethiopia) which is quite large.

`management_practice` currently has 6 accepted values:

1. `combined`: retrieve a single `.csv` output file combining all 4 management practices
2. `separate`: retreive a `.zip` file containing all 4 management practices in their own respective `.csv` files.
3. `maize_rf_highN`: retrieve a single output `.csv` for a high nitrogen management practice
4. `maize_irrig`: retrieve a single output `.csv` for an irrigated, high nitrogen management practice
5. `maize_rf_0N`: retrieve a single output `.csv` for a subsistence management practice
6. `maize_rf_lowN`: retrieve a single output `.csv` for a low nitrogen management practice

The earliest possible `start_year` is 1984. You may run DSSAT through 2018; if `start_year` is specified but `number_years` is not then the default will be to run from the specified `start_year` through 2018. If `start_year + number_years > 2018` it will default to running through 2018. If `start_year` is not specified then DSSAT will default to running from 1984 through 2018.

```
{
   "config":{
      "samples":10,
      "start_year": 2015,
      "number_years": 2,
      "management_practice": "maize_rf_highN"
   },
   "name":"DSSAT"
}
```


### Atlas

The Atlas.ai consumption model and asset wealth model are available as runs in MaaS, but are not currently executable. The runs are static geospatially and temporally. They are called `consumption_model` and `asset_wealth_model`.


### CHIRPS and CHIRPS-GEFS

CHIRPS historic weather data and CHIRPS-GEFS forecasts can be accessed by a configuration with the following three parameters:

`_type` should be one of `['mm_data','mm_anomaly','none_z-score']`. `mm_data` is the CHIRPS estimates of precipitation. The `mm_anomaly` provides the data value minus the mean of the entire time series up to the previous year. `none_z-score` provides the Standardized Precipitation Indexes ([SPI](https://climatedataguide.ucar.edu/climate-data/standardized-precipitation-index-spi)) of the estimates.

`dekad` is a zero padded value for the dekad of the year, `01-36` (a 10 day period).

`year` is the year in `YYYY` format for the data of interest.

`bbox` is the geospatial bounding box of interest. It should represent 4-elements in the WGS84 coordinate system: `[xmin, ymin, xmax, ymax]`. `x` is longitude, `y` is latitude. In other words, the coordinates of a SW point and a NE point define your region of interest.

```
{
   "config":{
      "_type": "mm_data",
      "dekad": "01",
      "year": 2019,
      "bbox": [33.512234, 2.719907, 49.981710, 16.501768]
   },
   "name":"CHIRPS"
}
```

For CHIRPS-GEFS, change the `name` parameter above from `CHIRPS` to `CHIRPS-GEFS`.

> **Note**: Both CHIRPS and CHIRPS-GEFS dekads have historical records. CHIRPS dates back to 1981 and the CHIRPS-GEFS dekads back to 1985.


### Yield Anomalies (LPJmL)

* `crop`: choose the crop of interest. It should be one of `[millet, maize, wheat]`
* `irrigation`: choose the irrigation level. It should be one of `[LIM, NO, POT]`. These correspond to:
   * `NO`: no irrigation anywhere. Crops are rain-fed only. This can be considered as a "what-if irrigation failed scenario".
   * `LIM`: irrigation is applied on crop-specific areas equipped for irrigation. Irrigation water withdrawal is limited to water available in surface water bodies. As a result, it is possible that irrigation demand cannot be fulfilled completely in some grid cells if demand is higher than supply.
   * `POT`: uses the same irrigated areas as LIM_IRRIGATION, but allows for withdrawals to exceed water available in surface water bodies. As a result, irrigated crops should not experience water stress.
* `nitrogen`: choose the nitrogen level. It should be one of `[LIM, LIM_p25, LIM_p50, UNLIM]`. These correspond to:
      * `LIM`: country- and crop-type-specific amounts of N fertilizer to crops. The dataset is from GGCMI (the Global Gridded Crop Model Inter-comparison within AgMIP) and describes fertilizer application levels around the year 2000.
      * `LIM_p25`: same as `LIM`, but with 25% more fertilizer in all cells where N>0. That is, cells without fertilization around 2000 in our data set do also not receive fertilizer in this scenario.
      * `LIM_p50`: similar to _p25, but with 50% more N.
      * `UNLIM`: extremely high N rates in all cells such that there should be no N limitation of crop growth. There are no negative effects of too much nitrogen on plant growth in our model (but there will be increased leaching and outgassing).
* `area`: either `global` (global pixel tif file) or `merged` (a txt file aggregated to the country level)
* `statistic`: *only provide if `area=global`*. Select the statistical aggregation over possible future climate realizations which can be any of `["mean", "std", "pctl,5", "pctl,95"]` for the mean, standard deviation, 5th percentile or 95th percentile. These four measures reflect the uncertainty of the climate forecasts starting in May 2018.

```
{
   "config":{
      "crop":"millet",
      "irrigation":"POT",
      "nitrogen":"UNLIM",
      "area":"global",
      "statistic":"pctl,95"
   },
   "name":"yield_anomalies_lpjml"
}
```

