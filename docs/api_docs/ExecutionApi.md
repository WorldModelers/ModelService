---
layout: default
parent: API
---

# ExecutionApi

All URIs are relative to *https://model-service.worldmodelers.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**available_results_get**](ExecutionApi.md#available_results_get) | **GET** /available_results | Obtain a list of run results
[**list_runs_model_name_get**](ExecutionApi.md#list_runs_model_name_get) | **GET** /list_runs/{ModelName} | Obtain a list of runs for a given model
[**result_file_result_file_name_get**](ExecutionApi.md#result_file_result_file_name_get) | **GET** /result_file/{ResultFileName} | Obtain the result file for a given model run.
[**run_model_post**](ExecutionApi.md#run_model_post) | **POST** /run_model | Run a model for a given a configuration
[**run_results_run_id_get**](ExecutionApi.md#run_results_run_id_get) | **GET** /run_results/{RunID} | Obtain metadata about the results of a given model run
[**run_status_run_id_get**](ExecutionApi.md#run_status_run_id_get) | **GET** /run_status/{RunID} | Obtain status for a given model run

# **available_results_get**
> list[RunResults] available_results_get(model_name=model_name, size=size)

Obtain a list of run results

Return a list of all available run results.

### Example
```python
import requests

params = (
    ('ModelName', 'DSSAT'),
    ('size', '5'),
)

response = requests.get('https://model-service.worldmodelers.com/available_results', params=params)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| A model name | [optional] 
 **size** | **int**| The maximum number of results to return. | [optional] 

### Return type

[**list[RunResults]**](RunResults.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_runs_model_name_get**
> list[RunID] list_runs_model_name_get(model_name)

Obtain a list of runs for a given model

Submit a `ModelName` and receive an array of `RunID`s associated with the given model.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/list_runs/DSSAT')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| A model name | 

### Return type

[**list[RunID]**](RunID.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **result_file_result_file_name_get**
> result_file_result_file_name_get(result_file_name)

Obtain the result file for a given model run.

Submit a `ResultFileName` and receive model run result file.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/result_file/95895fd4baa0a586e48d919e68dfbce0486ba9f3f7b137be4c39d14b42233.geojson')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **result_file_name** | [**ResultFileName**](.md)| A file name of a result file. | 

### Return type

void (empty response body)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **run_model_post**
> RunID run_model_post(body)

Run a model for a given a configuration

Submit a configuration to run a specific model. Model is run asynchronously. Results are available through `/run_results` endpoint. Note that the `requestBody` must include a `config` object which should have as its `keys` the appropriate model `parameter` `labels`. Each `key` should have a corresponding `parameter` `value`. If a `parameter` is missing it will be defaulted.

### Example
```python
import requests

data = {
       "config":{
          "country":"Ethiopia",
          "month":11,
          "rainfall_scenario":"high",
          "year":2017
       
    },
       "name":"malnutrition_model"
    }

response = requests.post('https://model-service.worldmodelers.com/run_model', json=data)

```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ModelConfig**](ModelConfig.md)| Model and configuration parameters | 

### Return type

[**RunID**](RunID.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **run_results_run_id_get**
> RunResults run_results_run_id_get(run_id)

Obtain metadata about the results of a given model run

Submit a `RunID` and receive model run results metadata, including whether it succeeded or failed and where to access the result data.

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/run_results/a05fca513dacf89c84616c503fb39ead119d0202a4e7461bde8b189c680f900f')
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **run_id** | [**RunID**](.md)| The ID for a given model run. | 

### Return type

[**RunResults**](RunResults.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **run_status_run_id_get**
> RunStatus run_status_run_id_get(run_id)

Obtain status for a given model run

Submit a `RunID` and receive the model run status

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/run_status/a05fca513dacf89c84616c503fb39ead119d0202a4e7461bde8b189c680f900f')

```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **run_id** | [**RunID**](.md)| The &#x60;ID&#x60; for a given model run. | 

### Return type

[**RunStatus**](RunStatus.md)

### Authorization

Basic auth required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

