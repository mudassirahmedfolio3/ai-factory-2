# api_client.api.OrdersApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**cancelOrder**](OrdersApi.md#cancelorder) | **POST** /orders/{orderId}/cancel | Cancel pending_payment order and release stock
[**completeMockPayment**](OrdersApi.md#completemockpayment) | **POST** /orders/{orderId}/complete-mock-payment | Demo pay-now (marks order paid, no Stripe)
[**createOrder**](OrdersApi.md#createorder) | **POST** /orders | Place order (pending_payment, reserves stock)
[**getOrderById**](OrdersApi.md#getorderbyid) | **GET** /orders/{orderId} | Get order detail
[**listOrders**](OrdersApi.md#listorders) | **GET** /orders | List my orders


# **cancelOrder**
> OrderDetail cancelOrder(orderId)

Cancel pending_payment order and release stock

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getOrdersApi();
final String orderId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.cancelOrder(orderId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling OrdersApi->cancelOrder: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orderId** | **String**|  | 

### Return type

[**OrderDetail**](OrderDetail.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **completeMockPayment**
> OrderDetail completeMockPayment(orderId)

Demo pay-now (marks order paid, no Stripe)

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getOrdersApi();
final String orderId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.completeMockPayment(orderId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling OrdersApi->completeMockPayment: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orderId** | **String**|  | 

### Return type

[**OrderDetail**](OrderDetail.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **createOrder**
> OrderDetail createOrder(createOrderRequest)

Place order (pending_payment, reserves stock)

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getOrdersApi();
final CreateOrderRequest createOrderRequest = ; // CreateOrderRequest | 

try {
    final response = api.createOrder(createOrderRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling OrdersApi->createOrder: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **createOrderRequest** | [**CreateOrderRequest**](CreateOrderRequest.md)|  | 

### Return type

[**OrderDetail**](OrderDetail.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getOrderById**
> OrderDetail getOrderById(orderId)

Get order detail

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getOrdersApi();
final String orderId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.getOrderById(orderId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling OrdersApi->getOrderById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orderId** | **String**|  | 

### Return type

[**OrderDetail**](OrderDetail.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listOrders**
> OrderListResponse listOrders(page, pageSize)

List my orders

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getOrdersApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listOrders(page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling OrdersApi->listOrders: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 24]

### Return type

[**OrderListResponse**](OrderListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

