# api_client.model.ProductDetail

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**name** | **String** |  | 
**brand** | **String** |  | 
**slug** | **String** |  | 
**description** | **String** |  | 
**category** | [**CategorySummary**](CategorySummary.md) |  | 
**price** | [**Money**](Money.md) |  | 
**compareAtPrice** | [**Money**](Money.md) |  | [optional] 
**primaryImageUrl** | **String** |  | 
**inStock** | **bool** |  | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 
**images** | [**BuiltList&lt;ProductImage&gt;**](ProductImage.md) |  | 
**specs** | [**LightingSpecs**](LightingSpecs.md) |  | 
**rating** | [**RatingSummary**](RatingSummary.md) |  | 
**popularityRank** | **int** |  | [optional] 
**unitsSold90Days** | **int** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


