---
layout: default
title: Model Execution
nav_order: 3
has_children: false
has_toc: false
---

# Model Execution
Models can be executed using the `/run_model` endpoint. To do this, you must provide a valid JSON configuration. Each model has a unique configuration that can be provided. 

You should use the `/model_config` endpoint to obtain a sample configuration for the model you are interested in executing.

You can then obtain information on each specifiable parameter through the `/model_parameters` endpoint.

## Examples
The [model-execution.ipynb](../notebooks/model-execution.ipynb) Jupyter Notebook walks through step by step how a model can be discovered and executed.