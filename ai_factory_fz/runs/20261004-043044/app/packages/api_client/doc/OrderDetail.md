# api_client.model.OrderDetail

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**orderNumber** | **String** |  | 
**status** | **String** |  | 
**customerStatusLabel** | **String** |  | 
**totalCents** | **int** |  | 
**currency** | **String** |  | 
**createdAt** | [**DateTime**](DateTime.md) |  | 
**items** | [**BuiltList&lt;OrderLineItem&gt;**](OrderLineItem.md) |  | 
**subtotalCents** | **int** |  | 
**shippingCents** | **int** |  | 
**discountCents** | **int** |  | 
**shippingAddress** | [**UkAddressInput**](UkAddressInput.md) |  | 
**tracking** | [**OrderDetailAllOfTracking**](OrderDetailAllOfTracking.md) |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


