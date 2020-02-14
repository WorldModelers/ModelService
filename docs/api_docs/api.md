---
layout: default
title: API
nav_order: 7
has_children: true
---

# MaaS API
This API specification is for the World Modelers Models as a Service (MaaS) System. The goal of this API is to provide a controller for model discovery and exploration, as well as for initializing and managing model runs.

## Documentation for API Endpoints

All URIs are relative to *https://model-service.worldmodelers.com*

Class | Method | HTTP request | Description
------------ | ------------- | ------------- | -------------
*ConceptsApi* | [**concept_mapping_get**](ConceptsApi.md#concept_mapping_get) | **GET** /concept_mapping | Obtain an array of models related to a concept.
*ConceptsApi* | [**list_concepts_get**](ConceptsApi.md#list_concepts_get) | **GET** /list_concepts | Obtain a list of available concepts
*ExecutionApi* | [**available_results_get**](ExecutionApi.md#available_results_get) | **GET** /available_results | Obtain a list of run results
*ExecutionApi* | [**list_runs_model_name_get**](ExecutionApi.md#list_runs_model_name_get) | **GET** /list_runs/{ModelName} | Obtain a list of runs for a given model
*ExecutionApi* | [**result_file_result_file_name_get**](ExecutionApi.md#result_file_result_file_name_get) | **GET** /result_file/{ResultFileName} | Obtain the result file for a given model run.
*ExecutionApi* | [**run_model_post**](ExecutionApi.md#run_model_post) | **POST** /run_model | Run a model for a given a configuration
*ExecutionApi* | [**run_results_run_id_get**](ExecutionApi.md#run_results_run_id_get) | **GET** /run_results/{RunID} | Obtain metadata about the results of a given model run
*ExecutionApi* | [**run_status_run_id_get**](ExecutionApi.md#run_status_run_id_get) | **GET** /run_status/{RunID} | Obtain status for a given model run
*ExplorationApi* | [**list_models_post**](ExplorationApi.md#list_models_post) | **POST** /list_models | Obtain a list of current models
*ExplorationApi* | [**model_config_model_name_get**](ExplorationApi.md#model_config_model_name_get) | **GET** /model_config/{ModelName} | Obtain configurations for a given model.
*ExplorationApi* | [**model_info_model_name_get**](ExplorationApi.md#model_info_model_name_get) | **GET** /model_info/{ModelName} | Get basic metadata information for a specified model.
*ExplorationApi* | [**model_outputs_model_name_get**](ExplorationApi.md#model_outputs_model_name_get) | **GET** /model_outputs/{ModelName} | Obtain information on a given model&#x27;s outputs.
*ExplorationApi* | [**model_parameters_model_name_get**](ExplorationApi.md#model_parameters_model_name_get) | **GET** /model_parameters/{ModelName} | Obtain information about a model&#x27;s parameters.

## Documentation For Models

 - [AvailableConcepts](AvailableConcepts.md)
 - [AvailableModels](AvailableModels.md)
 - [Concept](Concept.md)
 - [ConceptMapping](ConceptMapping.md)
 - [ConceptName](ConceptName.md)
 - [Model](Model.md)
 - [ModelConfig](ModelConfig.md)
 - [ModelName](ModelName.md)
 - [Parameter](Parameter.md)
 - [ResultFileName](ResultFileName.md)
 - [RunID](RunID.md)
 - [RunResults](RunResults.md)
 - [RunStatus](RunStatus.md)
 - [Variable](Variable.md)

## Documentation For Authorization

Please contact MaaS maintainers for authorization information.


## BasicAuth

- **Type**: HTTP basic authentication


## Author


