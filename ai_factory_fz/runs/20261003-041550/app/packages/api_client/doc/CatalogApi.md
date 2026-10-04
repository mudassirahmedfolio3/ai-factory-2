# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProductById**](CatalogApi.md#getproductbyid) | **GET** /products/{productId} | Get product detail
[**listCategories**](CatalogApi.md#listcategories) | **GET** /categories | List categories
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List products


# **getProductById**
> ProductDetail getProductById(productId)

Get product detail

Product detail including description, images, and variants with per-variant stock.

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.getProductById(productId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->getProductById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **productId** | **String**|  | 

### Return type

[**ProductDetail**](ProductDetail.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listCategories**
> CategoryListResponse listCategories(page, pageSize)

List categories

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listCategories(page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listCategories: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 20]

### Return type

[**CategoryListResponse**](CategoryListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listProducts**
> ProductListResponse listProducts(page, pageSize, categoryId)

List products

Paginated product summaries for the browse screen. Prices in integer cents USD.

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 
final String categoryId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | Optional category filter

try {
    final response = api.listProducts(page, pageSize, categoryId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listProducts: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 20]
 **categoryId** | **String**| Optional category filter | [optional] 

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

