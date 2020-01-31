---
layout: default
parent: API Models
---

# Parameter

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The name of the parameter | 
**description** | **str** | Natural language description of parameter | 
**type** | **str** | The parameter&#x27;s type | [optional] 
**default_value** | [**Object**](Object.md) | The parameter&#x27;s default value. Type depends on the parameter&#x27;s type. | [optional] 
**minimum** | [**Object**](Object.md) | The parameter&#x27;s minimum allowed value. Type depends on the parameter&#x27;s type. | [optional] 
**maximum** | [**Object**](Object.md) | The parameter&#x27;s maximum allowed value. Type depends on the parameter&#x27;s type. | [optional] 
**choices** | [**list[Object]**](Object.md) | An array of choices available for a parameter of type ChoiceParameter | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

