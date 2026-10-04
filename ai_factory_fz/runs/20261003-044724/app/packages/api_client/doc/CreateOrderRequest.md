# api_client.model.CreateOrderRequest

## Load the model package
```dart
import 'package:api_client/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**shippingAddress** | [**ShippingAddress**](ShippingAddress.md) |  | 
**couponCode** | **String** |  | [optional] 
**useServerCart** | **bool** |  | [optional] [default to true]
**lines** | [**BuiltList&lt;CartLineInput&gt;**](CartLineInput.md) |  | [optional] 
**idempotencyKey** | **String** |  | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


