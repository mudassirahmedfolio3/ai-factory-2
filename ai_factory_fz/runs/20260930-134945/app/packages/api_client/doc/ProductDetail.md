# api_client.model.ProductDetail

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**sku** | **String** |  | 
**name** | **String** |  | 
**brand** | **String** |  | 
**category** | [**Category**](Category.md) |  | 
**priceMinor** | **int** | Regular price in minor units (pence), VAT inclusive | 
**salePriceMinor** | **int** | Sale price in minor units, VAT inclusive; null when not on sale; always lower than priceMinor | 
**currency** | **String** |  | 
**stockQuantity** | **int** |  | 
**stockStatus** | [**StockStatus**](StockStatus.md) |  | 
**imageUrl** | **String** |  | 
**imageAlt** | **String** |  | 
**description** | **String** |  | 
**specifications** | [**LightingSpecifications**](LightingSpecifications.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


