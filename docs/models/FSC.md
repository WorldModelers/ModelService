---
layout: default
parent: Models Overview
---

# Food Shocks Cascade

Food Shocks Cascade (FSC) is executable through MaaS using a Docker container which Jataware generated in collaboration with Columbia University. However, this Docker container produces a complex set of outputs which was not relevant for the January Experiment. Instead, Columbia provided a pre-run set of outputs which were in a simplified format driven by the needs of the Experiment use case. So, execution of FSC has been disabled in MaaS for the time being.

Currently, FSC is limited to **wheat only**.

## Format

FSC outputs are all `.csv` files. It's inputs are also `.csv` files. The pre-run output for FSC is [available here](https://github.com/WorldModelers/ModelService/blob/master/FSC-Integration/FSC.csv).

## Resolution

FSC output is at the country-level and is annual.

## Processing

The MaaS controller for FSC is called [`fsc.py`](https://github.com/WorldModelers/ModelService/blob/master/REST-Server/openapi_server/fsc.py). This is currently disabled in favor of the pre-run output provided by Columbia. That output was processed with the [`FSC_processing.py` script](https://github.com/WorldModelers/ModelService/blob/master/FSC-Integration/FSC_processing.py).

## Issues/Lessons Learned

- FSC is a relatively lightweight R based model. It is easy to execute but currently its executable Docker container does not output data in the same format as has been provided by Columbia for its [pre-run output](https://github.com/WorldModelers/ModelService/blob/master/FSC-Integration/FSC.csv). Once Columbia updates the Docker container to produce output in this format it should be trivial to pull the updated container and turn back on FSC.
- FSC was an example of a model that required thresholding for visualization purposes. The "shock severity" output variable was based on thresholds set by Columbia; these were adjusted after Columbia determined that the thresholds they set did not provide sufficient visual differentiation between severity levels.