# api_client.api.WishlistApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getWishlist**](WishlistApi.md#getwishlist) | **GET** /wishlist | Get signed-in wishlist
[**importWishlist**](WishlistApi.md#importwishlist) | **POST** /wishlist/import | Import local guest wishlist product IDs
[**replaceWishlist**](WishlistApi.md#replacewishlist) | **PUT** /wishlist | Replace wishlist product IDs


# **getWishlist**
> WishlistResponse getWishlist()

Get signed-in wishlist

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();

try {
    final response = api.getWishlist();
    print(response);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->getWishlist: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**WishlistResponse**](WishlistResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **importWishlist**
> WishlistResponse importWishlist(importWishlistRequest)

Import local guest wishlist product IDs

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();
final ImportWishlistRequest importWishlistRequest = ; // ImportWishlistRequest | 

try {
    final response = api.importWishlist(importWishlistRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->importWishlist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **importWishlistRequest** | [**ImportWishlistRequest**](ImportWishlistRequest.md)|  | 

### Return type

[**WishlistResponse**](WishlistResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **replaceWishlist**
> WishlistResponse replaceWishlist(replaceWishlistRequest)

Replace wishlist product IDs

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();
final ReplaceWishlistRequest replaceWishlistRequest = ; // ReplaceWishlistRequest | 

try {
    final response = api.replaceWishlist(replaceWishlistRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->replaceWishlist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **replaceWishlistRequest** | [**ReplaceWishlistRequest**](ReplaceWishlistRequest.md)|  | 

### Return type

[**WishlistResponse**](WishlistResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

