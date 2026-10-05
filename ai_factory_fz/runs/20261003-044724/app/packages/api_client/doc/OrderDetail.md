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
**createdAt** | [**DateTime**](DateTime.md) |  | 
**shopperStatus** | [**ShopperOrderStatus**](ShopperOrderStatus.md) |  | 
**backendStatus** | **String** |  | 
**lines** | [**BuiltList&lt;OrderLineItem&gt;**](OrderLineItem.md) |  | 
**subtotal** | [**Money**](Money.md) |  | 
**discount** | [**Money**](Money.md) |  | 
**shipping** | [**Money**](Money.md) |  | 
**tax** | [**Money**](Money.md) |  | 
**total** | [**Money**](Money.md) |  | 
**couponCode** | **String** |  | [optional] 
**shippingAddress** | [**ShippingAddress**](ShippingAddress.md) |  | 
**carrierName** | **String** |  | [optional] 
**trackingNumber** | **String** |  | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


