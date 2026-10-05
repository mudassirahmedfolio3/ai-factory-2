# api_client.model.ProductVariant

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**sku** | **String** |  | 
**name** | **String** | Variant label (e.g. finish or size) | 
**price** | [**Money**](Money.md) |  | 
**stockQuantity** | **int** | Available stock for this variant (static in M1 mock) | 
**imageUrl** | **String** |  | [optional] 
**isDefault** | **bool** | Default variant used for list/detail price and availability | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


