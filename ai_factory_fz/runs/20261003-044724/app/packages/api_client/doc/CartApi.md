# api_client.api.CartApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getCart**](CartApi.md#getcart) | **GET** /cart | Get signed-in user cart
[**mergeCart**](CartApi.md#mergecart) | **POST** /cart/merge | Merge guest cart lines into account cart
[**replaceCart**](CartApi.md#replacecart) | **PUT** /cart | Replace cart items (full sync)


# **getCart**
> CartResponse getCart()

Get signed-in user cart

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();

try {
    final response = api.getCart();
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->getCart: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **mergeCart**
> CartResponse mergeCart(mergeCartRequest)

Merge guest cart lines into account cart

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final MergeCartRequest mergeCartRequest = ; // MergeCartRequest | 

try {
    final response = api.mergeCart(mergeCartRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->mergeCart: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **mergeCartRequest** | [**MergeCartRequest**](MergeCartRequest.md)|  | 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replaceCart**
> CartResponse replaceCart(replaceCartRequest)

Replace cart items (full sync)

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final ReplaceCartRequest replaceCartRequest = ; // ReplaceCartRequest | 

try {
    final response = api.replaceCart(replaceCartRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->replaceCart: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **replaceCartRequest** | [**ReplaceCartRequest**](ReplaceCartRequest.md)|  | 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

