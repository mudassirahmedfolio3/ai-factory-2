# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProductById**](CatalogApi.md#getproductbyid) | **GET** /products/{productId} | Get product detail
[**listCategories**](CatalogApi.md#listcategories) | **GET** /categories | List product categories
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List products


# **getProductById**
> ProductDetail getProductById(productId)

Get product detail

Returns full product detail including category and active variants with per-variant stock. Supports US-002. Public endpoint. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | Product UUID

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
 **productId** | **String**| Product UUID | 

### Return type

[**ProductDetail**](ProductDetail.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listCategories**
> CategoryListResponse listCategories()

List product categories

Returns retail categories used for browse filters (e.g. Apparel, Accessories, Home, Essentials). Public endpoint; supports US-001 filters. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();

try {
    final response = api.listCategories();
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listCategories: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**CategoryListResponse**](CategoryListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listProducts**
> ProductListResponse listProducts(page, pageSize, q, categorySlug, inStockOnly, sort)

List products

Paginated product listing with optional category filter and search. Supports US-001 browse requirements. Public endpoint; no authentication required. Prices are tax-inclusive integer minor units with ISO 4217 currency. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 1-based page number
final int pageSize = 56; // int | Items per page
final String q = q_example; // String | Case-insensitive search against product name and description
final String categorySlug = apparel; // String | Filter by category slug (e.g. apparel, accessories, home, essentials)
final bool inStockOnly = true; // bool | When true, exclude products with no in-stock active variants
final String sort = sort_example; // String | Sort order for results

try {
    final response = api.listProducts(page, pageSize, q, categorySlug, inStockOnly, sort);
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
 **q** | **String**| Case-insensitive search against product name and description | [optional] 
 **categorySlug** | **String**| Filter by category slug (e.g. apparel, accessories, home, essentials) | [optional] 
 **inStockOnly** | **bool**| When true, exclude products with no in-stock active variants | [optional] [default to false]
 **sort** | **String**| Sort order for results | [optional] [default to 'newest']

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

