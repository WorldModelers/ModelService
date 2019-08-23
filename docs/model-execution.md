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
```
{
   "config":{
      "percent_of_normal_rainfall":100.0
   },
   "name":"malnutrition_model"
}
```

### Food Shocks Cascade Model

```
{
   "config":{
      "country":"USA",
      "fractional_reserve_access":0.8,
      "production_decrease":0.2,
      "run_id":"cf49488892ea86c77f0f0a4176e73cfa112b52db9126d9236db9f4d3e0e21a17",
      "year":2005
   },
   "name":"FSC"
}
```

### DSSAT

Note that `samples` denotes the number of pixel predictions DSSAT will make. Setting `samples` to `0` returns the entire geography (all Ethiopia) which is quite large.

```
{
   "config":{
      "samples":10
   },
   "name":"DSSAT"
}
```