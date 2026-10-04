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
**category** | [**Category**](Category.md) |  | 
**price** | [**Money**](Money.md) | Display price (default or lowest active variant), tax-inclusive | 
**primaryImageUrl** | **String** |  | 
**inStock** | **bool** | True when at least one active variant has stockQuantity > 0 | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


