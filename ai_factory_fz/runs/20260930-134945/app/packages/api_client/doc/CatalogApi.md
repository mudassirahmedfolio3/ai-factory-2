# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://localhost:3000*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProduct**](CatalogApi.md#getproduct) | **GET** /api/v1/products/{productId} | Get one active product with lighting specifications
[**listProducts**](CatalogApi.md#listproducts) | **GET** /api/v1/products | List active products


# **getProduct**
> ProductDetail getProduct(productId)

Get one active product with lighting specifications

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | Product UUID

try {
    final response = api.getProduct(productId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->getProduct: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **productId** | **String**| Product UUID | 

### Return type

[**ProductDetail**](ProductDetail.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listProducts**
> ProductPage listProducts(page, pageSize)

List active products

Returns active products ordered by name ascending, then id ascending.

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 1-based page number
final int pageSize = 56; // int | Items per page

try {
    final response = api.listProducts(page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listProducts: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| 1-based page number | [optional] [default to 1]
 **pageSize** | **int**| Items per page | [optional] [default to 20]

### Return type

[**ProductPage**](ProductPage.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

