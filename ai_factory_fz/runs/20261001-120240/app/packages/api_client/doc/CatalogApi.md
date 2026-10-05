# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProductById**](CatalogApi.md#getproductbyid) | **GET** /products/{productId} | Get product detail
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List men&#39;s shirts


# **getProductById**
> ProductDetail getProductById(productId)

Get product detail

Returns full product detail including all active variants. Supports US-002 product detail requirements. Public endpoint. 

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

# **listProducts**
> ProductListResponse listProducts(page, pageSize, q, size, color, shirtType, minPriceCents, maxPriceCents, sort)

List men's shirts

Paginated product listing with optional filters and search. Supports US-001 browse requirements. Public endpoint; no authentication required. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 1-based page number
final int pageSize = 56; // int | Items per page
final String q = q_example; // String | Case-insensitive search against product title and description
final ShirtSize size = ; // ShirtSize | Filter to products with at least one variant in this size
final String color = Navy; // String | Filter to products with at least one variant in this color
final ShirtType shirtType = ; // ShirtType | Filter by shirt type/category style
final int minPriceCents = 2000; // int | Minimum variant price in USD cents (inclusive)
final int maxPriceCents = 4500; // int | Maximum variant price in USD cents (inclusive)
final String sort = sort_example; // String | Sort order for results

try {
    final response = api.listProducts(page, pageSize, q, size, color, shirtType, minPriceCents, maxPriceCents, sort);
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
 **q** | **String**| Case-insensitive search against product title and description | [optional] 
 **size** | [**ShirtSize**](.md)| Filter to products with at least one variant in this size | [optional] 
 **color** | **String**| Filter to products with at least one variant in this color | [optional] 
 **shirtType** | [**ShirtType**](.md)| Filter by shirt type/category style | [optional] 
 **minPriceCents** | **int**| Minimum variant price in USD cents (inclusive) | [optional] 
 **maxPriceCents** | **int**| Maximum variant price in USD cents (inclusive) | [optional] 
 **sort** | **String**| Sort order for results | [optional] [default to 'newest']

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

