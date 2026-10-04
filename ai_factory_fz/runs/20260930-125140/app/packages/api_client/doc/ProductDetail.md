# api_client.model.ProductDetail

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**slug** | **String** |  | 
**name** | **String** |  | 
**description** | **String** |  | 
**imageUrl** | **String** |  | 
**imageAlt** | **String** |  | 
**priceFrom** | [**Money**](Money.md) |  | 
**inStock** | **bool** |  | 
**sizes** | **BuiltList&lt;String&gt;** | Distinct sizes across active variants, in display order | 
**colors** | **BuiltList&lt;String&gt;** | Distinct colors across active variants, in display order | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


