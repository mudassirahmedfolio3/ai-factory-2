# api_client.model.ProductSummary

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**name** | **String** |  | 
**price** | [**Money**](Money.md) |  | 
**thumbnailUrl** | **String** | Thumbnail image URL; null means the client shows a placeholder | 
**inStock** | **bool** | True when stockQuantity is greater than 0 | 
**stockQuantity** | **int** | Available stock of the default variant | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


