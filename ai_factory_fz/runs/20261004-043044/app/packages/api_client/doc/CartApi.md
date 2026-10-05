# api_client.api.CartApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addCartItem**](CartApi.md#addcartitem) | **POST** /cart/items | Add cart line
[**getCart**](CartApi.md#getcart) | **GET** /cart | Get cart
[**mergeGuestCart**](CartApi.md#mergeguestcart) | **POST** /cart/merge | Merge guest cart after login
[**removeCartItem**](CartApi.md#removecartitem) | **DELETE** /cart/items/{itemId} | Remove line
[**updateCartItem**](CartApi.md#updatecartitem) | **PATCH** /cart/items/{itemId} | Update quantity


# **addCartItem**
> CartResponse addCartItem(addCartItemRequest, xGuestCartId)

Add cart line

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final AddCartItemRequest addCartItemRequest = ; // AddCartItemRequest | 
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.addCartItem(addCartItemRequest, xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->addCartItem: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addCartItemRequest** | [**AddCartItemRequest**](AddCartItemRequest.md)|  | 
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCart**
> CartResponse getCart(xGuestCartId)

Get cart

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.getCart(xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->getCart: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **mergeGuestCart**
> CartResponse mergeGuestCart(xGuestCartId)

Merge guest cart after login

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.mergeGuestCart(xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->mergeGuestCart: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **removeCartItem**
> CartResponse removeCartItem(itemId, xGuestCartId)

Remove line

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final String itemId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.removeCartItem(itemId, xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->removeCartItem: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **itemId** | **String**|  | 
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateCartItem**
> CartResponse updateCartItem(itemId, updateCartItemRequest, xGuestCartId)

Update quantity

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCartApi();
final String itemId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 
final UpdateCartItemRequest updateCartItemRequest = ; // UpdateCartItemRequest | 
final String xGuestCartId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.updateCartItem(itemId, updateCartItemRequest, xGuestCartId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CartApi->updateCartItem: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **itemId** | **String**|  | 
 **updateCartItemRequest** | [**UpdateCartItemRequest**](UpdateCartItemRequest.md)|  | 
 **xGuestCartId** | **String**|  | [optional] 

### Return type

[**CartResponse**](CartResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

