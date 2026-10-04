# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getCatalogFacets**](CatalogApi.md#getcatalogfacets) | **GET** /catalog/facets | Filter facet metadata
[**getCategoryBySlug**](CatalogApi.md#getcategorybyslug) | **GET** /categories/{slug} | Get category by slug
[**getHome**](CatalogApi.md#gethome) | **GET** /home | Home merchandising payload
[**getProductById**](CatalogApi.md#getproductbyid) | **GET** /products/{productId} | Product detail
[**listCategories**](CatalogApi.md#listcategories) | **GET** /categories | List category tree
[**listProductReviews**](CatalogApi.md#listproductreviews) | **GET** /products/{productId}/reviews | List product reviews
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List and search products


# **getCatalogFacets**
> CatalogFacetsResponse getCatalogFacets(categorySlug)

Filter facet metadata

Brands, finishes, wattage bounds, and category options for the listing filter UI (US-003).

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String categorySlug = categorySlug_example; // String | 

try {
    final response = api.getCatalogFacets(categorySlug);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->getCatalogFacets: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **categorySlug** | **String**|  | [optional] 

### Return type

[**CatalogFacetsResponse**](CatalogFacetsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCategoryBySlug**
> CategoryDetail getCategoryBySlug(slug)

Get category by slug

Resolve a category or subcategory for listing context (US-001).

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String slug = slug_example; // String | 

try {
    final response = api.getCategoryBySlug(slug);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->getCategoryBySlug: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **slug** | **String**|  | 

### Return type

[**CategoryDetail**](CategoryDetail.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getHome**
> HomeResponse getHome()

Home merchandising payload

Top-level categories and featured products for the home screen (US-001).

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();

try {
    final response = api.getHome();
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->getHome: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**HomeResponse**](HomeResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getProductById**
> ProductDetail getProductById(productId)

Product detail

Detail with variants, lighting specifications, images, and ratings summary (US-004).

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
> CategoryListResponse listCategories(depth)

List category tree

Returns active categories with optional parent relationships for browse paths (US-001).

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int depth = 56; // int | 1 for top-level only, 2 includes children

try {
    final response = api.listCategories(depth);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listCategories: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **depth** | **int**| 1 for top-level only, 2 includes children | [optional] [default to 2]

### Return type

[**CategoryListResponse**](CategoryListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listProductReviews**
> ReviewListResponse listProductReviews(productId, page, pageSize)

List product reviews

Paginated reviews for product detail (US-004).

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listProductReviews(productId, page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CatalogApi->listProductReviews: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **productId** | **String**|  | 
 **page** | **int**|  | [optional] [default to 1]
 **pageSize** | **int**|  | [optional] [default to 20]

### Return type

[**ReviewListResponse**](ReviewListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **listProducts**
> ProductListResponse listProducts(page, pageSize, q, categorySlug, brand, minPriceCents, maxPriceCents, minWattage, maxWattage, finish, inStockOnly, sort)

List and search products

Paginated product listing with text search (name, SKU, brand, keywords), filters, and sort (US-001, US-002, US-003). Prices in pence GBP. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 
final int pageSize = 56; // int | 
final String q = q_example; // String | Search query (name, SKU, brand, description)
final String categorySlug = categorySlug_example; // String | 
final BuiltList<String> brand = ; // BuiltList<String> | Repeat for multiple brands
final int minPriceCents = 56; // int | 
final int maxPriceCents = 56; // int | 
final int minWattage = 56; // int | 
final int maxWattage = 56; // int | 
final String finish = finish_example; // String | 
final bool inStockOnly = true; // bool | 
final ProductSort sort = ; // ProductSort | 

try {
    final response = api.listProducts(page, pageSize, q, categorySlug, brand, minPriceCents, maxPriceCents, minWattage, maxWattage, finish, inStockOnly, sort);
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
 **q** | **String**| Search query (name, SKU, brand, description) | [optional] 
 **categorySlug** | **String**|  | [optional] 
 **brand** | [**BuiltList&lt;String&gt;**](String.md)| Repeat for multiple brands | [optional] 
 **minPriceCents** | **int**|  | [optional] 
 **maxPriceCents** | **int**|  | [optional] 
 **minWattage** | **int**|  | [optional] 
 **maxWattage** | **int**|  | [optional] 
 **finish** | **String**|  | [optional] 
 **inStockOnly** | **bool**|  | [optional] [default to false]
 **sort** | [**ProductSort**](.md)|  | [optional] 

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

