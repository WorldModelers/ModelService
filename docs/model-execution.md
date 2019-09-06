# Model Execution
Models can be executed using the `/run_model` endpoint. To do this, you must provide a valid JSON configuration. Each model has a unique configuration that can be provided. Below are example configurations for each model.

## Contents

- [Kimetrica Population Model](#kimetrica-population-model)
- [Kimetrica Malnutrition Model](#kimetrica-malnutrition-model)
- [Food Shocks Cascade Model](#food-shocks-cascade-model)
- [DSSAT](#DSSAT)
- [Atlas](#Atlas)
- [CHIRPS](#CHIRPS)

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


### CHIRPS

CHIRPS weather data can be accessed by a configuration with the following three parameters:

`_type` should be one of `['mm_data','mm_anomaly','none_z-score']`. `mm_data` is the CHIRPS estimates of precipitation. The `mm_anomaly` provides the data value minus the mean of the entire time series up to the previous year. `none_z-score` provides the Standardized Precipitation Indexes ([SPI](https://climatedataguide.ucar.edu/climate-data/standardized-precipitation-index-spi)) of the estimates.

`dekad` is a zero padded value for the dekad of the year, `01-36` (a 10 day period).

`year` is the year in `YYYY` format for the data of interest.

```
{
   "config":{
      "_type": 'mm_data',
      "dekad": '01',
      "year": 2019
   },
   "name":"CHIRPS"
}
```

> **Note**: CHIRPS is available for Ethiopia only at the moment. Data is available from 1981 through near present.