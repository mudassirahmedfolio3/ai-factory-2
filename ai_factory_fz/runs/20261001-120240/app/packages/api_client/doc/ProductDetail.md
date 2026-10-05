# api_client.model.ProductDetail

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**title** | **String** |  | 
**description** | **String** |  | 
**shirtType** | [**ShirtType**](ShirtType.md) |  | 
**fitType** | [**FitType**](FitType.md) |  | 
**price** | [**Money**](Money.md) | Default display price (lowest variant) | 
**primaryImageUrl** | **String** |  | 
**variants** | [**BuiltList&lt;ProductVariant&gt;**](ProductVariant.md) |  | 
**returnsPolicyText** | **String** | 30-day returns policy for display on detail screen | 
**averageRating** | **double** |  | [optional] 
**reviewCount** | **int** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


