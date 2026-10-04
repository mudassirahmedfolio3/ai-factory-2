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
**description** | **String** |  | 
**price** | [**Money**](Money.md) |  | 
**imageUrl** | **String** | Full-size image URL; null means the client shows a placeholder | 
**thumbnailUrl** | **String** |  | 
**inStock** | **bool** | True when stockQuantity is greater than 0 | 
**stockQuantity** | **int** |  | 
**defaultVariantId** | **String** | Id of the product's default variant (stock is tracked per variant) | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


