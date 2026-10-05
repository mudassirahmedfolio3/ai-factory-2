# api_client.model.Product

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
**brand** | **String** |  | 
**description** | **String** |  | 
**productType** | [**ProductType**](ProductType.md) |  | 
**category** | [**Category**](Category.md) |  | 
**images** | [**BuiltList&lt;Image&gt;**](Image.md) |  | 
**ratingAverage** | **num** | Average rating with one decimal; null when there are no ratings. Display only. | 
**ratingCount** | **int** |  | 
**specifications** | [**LightingSpecifications**](LightingSpecifications.md) |  | 
**defaultVariantId** | **String** | Id of the variant with isDefault true. | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


