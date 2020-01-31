---
layout: default
parent: MaaS API
---

# swagger_client.ExplorationApi

All URIs are relative to *https://model-service.worldmodelers.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**list_models_post**](ExplorationApi.md#list_models_post) | **POST** /list_models | Obtain a list of current models
[**model_config_model_name_get**](ExplorationApi.md#model_config_model_name_get) | **GET** /model_config/{ModelName} | Obtain configurations for a given model.
[**model_info_model_name_get**](ExplorationApi.md#model_info_model_name_get) | **GET** /model_info/{ModelName} | Get basic metadata information for a specified model.
[**model_outputs_model_name_get**](ExplorationApi.md#model_outputs_model_name_get) | **GET** /model_outputs/{ModelName} | Obtain information on a given model&#x27;s outputs.
[**model_parameters_model_name_get**](ExplorationApi.md#model_parameters_model_name_get) | **GET** /model_parameters/{ModelName} | Obtain information about a model&#x27;s parameters.

# **list_models_post**
> AvailableModels list_models_post()

Obtain a list of current models

Request a list of currently available models.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ExplorationApi()

try:
    # Obtain a list of current models
    api_response = api_instance.list_models_post()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ExplorationApi->list_models_post: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AvailableModels**](AvailableModels.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_config_model_name_get**
> ModelConfig model_config_model_name_get(model_name)

Obtain configurations for a given model.

Submit a model name and receive all configurations for the given model.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ExplorationApi()
model_name = swagger_client.ModelName() # ModelName | The name of a model.

try:
    # Obtain configurations for a given model.
    api_response = api_instance.model_config_model_name_get(model_name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ExplorationApi->model_config_model_name_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**ModelConfig**](ModelConfig.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_info_model_name_get**
> Model model_info_model_name_get(model_name)

Get basic metadata information for a specified model.

Submit a model name and receive metadata information about the model, such as its purpose, who maintains it, and how it can be run.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ExplorationApi()
model_name = swagger_client.ModelName() # ModelName | The name of a model.

try:
    # Get basic metadata information for a specified model.
    api_response = api_instance.model_info_model_name_get(model_name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ExplorationApi->model_info_model_name_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**Model**](Model.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_outputs_model_name_get**
> list[Variable] model_outputs_model_name_get(model_name)

Obtain information on a given model's outputs.

Submit a model name and receive information about the output variables produced by this model.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ExplorationApi()
model_name = swagger_client.ModelName() # ModelName | The name of a model.

try:
    # Obtain information on a given model's outputs.
    api_response = api_instance.model_outputs_model_name_get(model_name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ExplorationApi->model_outputs_model_name_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**list[Variable]**](Variable.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **model_parameters_model_name_get**
> list[Parameter] model_parameters_model_name_get(model_name)

Obtain information about a model's parameters.

Submit a model name and receive information about the parameters used by this model. Specific parameters are used on a per-configuration basis.

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.ExplorationApi()
model_name = swagger_client.ModelName() # ModelName | The name of a model.

try:
    # Obtain information about a model's parameters.
    api_response = api_instance.model_parameters_model_name_get(model_name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ExplorationApi->model_parameters_model_name_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **model_name** | [**ModelName**](.md)| The name of a model. | 

### Return type

[**list[Parameter]**](Parameter.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

