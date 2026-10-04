# api_client.model.ProductSummary

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**title** | **String** |  | 
**shirtType** | [**ShirtType**](ShirtType.md) |  | 
**fitType** | [**FitType**](FitType.md) |  | 
**price** | [**Money**](Money.md) | Lowest active variant price for display | 
**primaryImageUrl** | **String** |  | 
**availableSizes** | [**BuiltList&lt;ShirtSize&gt;**](ShirtSize.md) |  | 
**availableColors** | **BuiltList&lt;String&gt;** |  | 
**averageRating** | **double** | Present post-M1 when reviews exist; omitted in M1 mock | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


