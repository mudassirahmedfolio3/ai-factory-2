# api_client.api.CheckoutApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createOrder**](CheckoutApi.md#createorder) | **POST** /checkout/orders | Create order and reserve stock
[**previewCheckout**](CheckoutApi.md#previewcheckout) | **POST** /checkout/preview | Preview totals and shipping


# **createOrder**
> CreateOrderResponse createOrder(idempotencyKey, createOrderRequest, xGuestCartId)

Create order and reserve stock

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCheckoutApi();
final String idempotencyKey = idempotencyKey_example; // String | 
final CreateOrderRequest createOrderRequest = ; // CreateOrderRequest | 
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.createOrder(idempotencyKey, createOrderRequest, xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CheckoutApi->createOrder: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **idempotencyKey** | **String**|  | 
 **createOrderRequest** | [**CreateOrderRequest**](CreateOrderRequest.md)|  | 
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CreateOrderResponse**](CreateOrderResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **previewCheckout**
> CheckoutPreviewResponse previewCheckout(checkoutPreviewRequest, xGuestCartId)

Preview totals and shipping

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCheckoutApi();
final CheckoutPreviewRequest checkoutPreviewRequest = ; // CheckoutPreviewRequest | 
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.previewCheckout(checkoutPreviewRequest, xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CheckoutApi->previewCheckout: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **checkoutPreviewRequest** | [**CheckoutPreviewRequest**](CheckoutPreviewRequest.md)|  | 
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CheckoutPreviewResponse**](CheckoutPreviewResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

