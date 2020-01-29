# Model Registration

This document describes the process for registering a model to MaaS. Throughout, it will refer to files included in the `registration` directory. This doc describes how to register a model with fixed output. In the future, this doc will also describe how to register a containerized, executable model.

> Containerization through Docker allows MaaS to execute arbitrary models. Though the remainder of the doc does not deal with executable models, the principals are largely the same for fixed vs. executable models.


## Metadata

To register a model, you first need to describe it. This is done through a descriptive metadata `YAML` file. The example that we will use is for a model called `ExampleModel` which predicts cereal and timber production based on various rainfall and temperature scenarios. You can see `ExampleModel`'s metadata file `example-model-metadata.yaml`. The metadata file must describe the output variables and the parameters used by the model that are of interest in MaaS.

To learn more about how to create a metadata `YAML` file you can refer to the [metadata docs](metadata.md).

> **A copy of this metadata file must be placed in the `metadata/models` so that it can be dynamically read by MaaS at run-time.** Additionally, you should validate your metadata file's schema following the instructions in the [metadata docs](metadata.md) prior to running MaaS.

## Model Outputs

For the purpose of this doc, we assume that your model's output is in `CSV` form. Each `CSV` should have the following mandatory columns:

* `datetime`: a timestamp in `YYYY-MM-DD` format
* `latitude`: the latitude associated with the model output
* `longitude`: the longitude associated with the model output

Additionally, the output should contain one column per output variable and parameter that was specified in the metadata file. So, for `ExampleModel` there will be the following columns:

* `rainfall`
* `temperature`
* `cereal_production`
* `timber_production`

Each file pertains to **a single model run** and is stored in the `example_runs` directory. Since each file pertains to only a single run, it should have constant values for the two parameter columns. For example, a run with `low` temperature and `medium` rainfall will have those columns fixed to those values. Since the parameters space for `ExampleModel` is 3 x 3, there are 9 total model runs in `example_runs`.


## Output Ingestion 

Now you are ready to ingest your model's output into MaaS. To do this, you can use the generic `example_processing.py` script. This script has two CLI arguments:

* the directory where you've stored your model runs
* the location of your metadata file

So, you can run this with:

```
python example_processing.py example_runs example-model-metadata.yaml
```

This will do 3 things:

1. Upload each run to S3 for long term storage
2. Generate a model run in Redis to support MaaS API endpoints
3. Normalize and ingest the run data into the MaaS database