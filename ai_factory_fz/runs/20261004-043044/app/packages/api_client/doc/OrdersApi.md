# api_client.api.OrdersApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getOrderById**](OrdersApi.md#getorderbyid) | **GET** /orders/{orderId} | Order detail
[**listOrders**](OrdersApi.md#listorders) | **GET** /orders | Order history


# **getOrderById**
> OrderDetail getOrderById(orderId)

Order detail

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

Order history

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
 **pageSize** | **int**|  | [optional] [default to 20]

### Return type

[**OrderListResponse**](OrderListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

