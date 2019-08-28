# Model Execution
Models can be executed using the `/run_model` endpoint. To do this, you must provide a valid JSON configuration. Each model has a unique configuration that can be provided. Below are example configurations for each model.

## Contents

- [Kimetrica Population Model](#kimetrica-population-model)
- [Kimetrica Malnutrition Model](#kimetrica-malnutrition-model)
- [Food Shocks Cascade Model](#food-shocks-cascade-model)
- [DSSAT](#DSSAT)

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

```
{
   "config":{
      "samples":10,
      "management_practice": "maize_rf_highN"
   },
   "name":"DSSAT"
}
```