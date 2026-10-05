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
**metal** | [**MetalTone**](MetalTone.md) |  | 
**occasion** | [**Occasion**](Occasion.md) |  | 
**price** | [**Money**](Money.md) | Display price (default or lowest active variant); 1999 cents USD for Tropical Earring | 
**primaryImageUrl** | **String** | Primary product image URL or placeholder asset URI | 
**inStock** | **bool** | True when at least one active variant has stockQuantity > 0 | 
**averageRating** | **num** | Aggregate star rating on a 1–5 scale; 0 when no reviews | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


