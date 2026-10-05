# api_client.api.WishlistApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addWishlistItem**](WishlistApi.md#addwishlistitem) | **POST** /wishlist/items | Add wishlist item
[**listWishlist**](WishlistApi.md#listwishlist) | **GET** /wishlist | List wishlist
[**removeWishlistItem**](WishlistApi.md#removewishlistitem) | **DELETE** /wishlist/items/{productId} | Remove wishlist item


# **addWishlistItem**
> WishlistItem addWishlistItem(addWishlistItemRequest)

Add wishlist item

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();
final AddWishlistItemRequest addWishlistItemRequest = ; // AddWishlistItemRequest | 

try {
    final response = api.addWishlistItem(addWishlistItemRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->addWishlistItem: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addWishlistItemRequest** | [**AddWishlistItemRequest**](AddWishlistItemRequest.md)|  | 

### Return type

[**WishlistItem**](WishlistItem.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listWishlist**
> WishlistListResponse listWishlist(page, pageSize)

List wishlist

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listWishlist(page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->listWishlist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 20]

### Return type

[**WishlistListResponse**](WishlistListResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **removeWishlistItem**
> removeWishlistItem(productId)

Remove wishlist item

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getWishlistApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    api.removeWishlistItem(productId);
} on DioException catch (e) {
    print('Exception when calling WishlistApi->removeWishlistItem: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **productId** | **String**|  | 

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

