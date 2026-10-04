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
**description** | **String** | Longer listing copy for the product detail screen | 
**category** | [**Category**](Category.md) |  | 
**metal** | [**MetalTone**](MetalTone.md) |  | 
**occasion** | [**Occasion**](Occasion.md) |  | 
**price** | [**Money**](Money.md) | Display price from default variant (1999 cents USD for Tropical Earring) | 
**primaryImageUrl** | **String** |  | 
**inStock** | **bool** |  | 
**averageRating** | **num** | Aggregate star rating; 0 when reviews is empty | 
**reviews** | [**BuiltList&lt;Review&gt;**](Review.md) | Mock reviews in M1; empty array triggers empty-reviews UI state | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 
**returnsPolicyText** | **String** | Optional returns policy for later checkout UI | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


