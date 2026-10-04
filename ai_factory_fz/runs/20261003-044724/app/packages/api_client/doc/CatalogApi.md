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
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List and search products


# **getProductById**
> ProductDetail getProductById(productId)

Get product detail

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
> CategoryListResponse listCategories()

List product categories

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
> ProductListResponse listProducts(page, pageSize, q, category, brand, minPriceCents, maxPriceCents, availability, sort)

List and search products

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 
final String q = q_example; // String | 
final String category = category_example; // String | 
final String brand = brand_example; // String | 
final int minPriceCents = 56; // int | 
final int maxPriceCents = 56; // int | 
final AvailabilityFilter availability = ; // AvailabilityFilter | 
final String sort = sort_example; // String | 

try {
    final response = api.listProducts(page, pageSize, q, category, brand, minPriceCents, maxPriceCents, availability, sort);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listProducts: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 24]
 **q** | **String**|  | [optional] 
 **category** | **String**|  | [optional] 
 **brand** | **String**|  | [optional] 
 **minPriceCents** | **int**|  | [optional] 
 **maxPriceCents** | **int**|  | [optional] 
 **availability** | [**AvailabilityFilter**](.md)|  | [optional] 
 **sort** | **String**|  | [optional] [default to 'newest']

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

