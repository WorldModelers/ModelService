---
layout: default
parent: API
---

# ConceptsApi

All URIs are relative to *https://model-service.worldmodelers.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**concept_mapping_get**](ConceptsApi.md#concept_mapping_get) | **GET** /concept_mapping | Obtain an array of models related to a concept.
[**list_concepts_get**](ConceptsApi.md#list_concepts_get) | **GET** /list_concepts | Obtain a list of available concepts

# **concept_mapping_get**
> ConceptMapping concept_mapping_get(concept=concept, concept_type=concept_type)

Obtain an array of models related to a concept.

Submit a concept name and optional type and receive an array of concepts related to that concept.       

### Example
```python
import requests

params = (
    ('concept', 'wm/concept/causal_factor/agriculture/planting'),
    ('concept_type', 'output'),
)

response = requests.get('https://model-service.worldmodelers.com/concept_mapping', params=params)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **concept** | [**ConceptName**](.md)| A concept name | [optional] 
 **concept_type** | **str**| The type of concept objects to return | [optional] 

### Return type

[**ConceptMapping**](ConceptMapping.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **list_concepts_get**
> AvailableConcepts list_concepts_get()

Obtain a list of available concepts

Request a list of currently available concepts. These are derived from the list of  [UN indicators](https://github.com/WorldModelers/Ontologies/blob/master/performer_ontologies/un_to_indicators.tsv) and are tied to model output variables. 

### Example
```python
import requests

response = requests.get('https://model-service.worldmodelers.com/list_concepts')
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**AvailableConcepts**](AvailableConcepts.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

