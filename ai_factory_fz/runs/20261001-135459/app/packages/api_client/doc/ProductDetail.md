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
**category** | [**Category**](Category.md) |  | 
**price** | [**Money**](Money.md) | Display price from default variant (tax-inclusive) | 
**primaryImageUrl** | **String** |  | 
**inStock** | **bool** |  | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 
**returnsPolicyText** | **String** | Optional return policy note for later UI (e.g. 14-day returns) | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


