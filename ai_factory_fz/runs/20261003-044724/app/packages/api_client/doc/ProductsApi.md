# api_client.api.ProductsApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProductById**](ProductsApi.md#getproductbyid) | **GET** /products/{productId} | Get a single product&#39;s detail including variants, availability and rating summary
[**listProducts**](ProductsApi.md#listproducts) | **GET** /products | List products with optional search, category and price-band filters, paginated


# **getProductById**
> ProductDetail getProductById(productId)

Get a single product's detail including variants, availability and rating summary

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getProductsApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 

try {
    final response = api.getProductById(productId);
    print(response);
} on DioException catch (e) {
    print('Exception when calling ProductsApi->getProductById: $e\n');
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

# **listProducts**
> ProductListResponse listProducts(search, categorySlug, priceBand, page, pageSize)

List products with optional search, category and price-band filters, paginated

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getProductsApi();
final String search = search_example; // String | Case-insensitive match against product name/description
final String categorySlug = categorySlug_example; // String | 
final PriceBand priceBand = ; // PriceBand | Predefined price band in cents (value ~500-2500, mid ~2500-7500, premium up to ~15000)
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listProducts(search, categorySlug, priceBand, page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling ProductsApi->listProducts: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **search** | **String**| Case-insensitive match against product name/description | [optional] 
 **categorySlug** | **String**|  | [optional] 
 **priceBand** | [**PriceBand**](.md)| Predefined price band in cents (value ~500-2500, mid ~2500-7500, premium up to ~15000) | [optional] 
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 20]

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

