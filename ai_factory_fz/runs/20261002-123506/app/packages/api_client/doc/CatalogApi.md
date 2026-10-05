# api_client.api.CatalogApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getProductById**](CatalogApi.md#getproductbyid) | **GET** /products/{productId} | Get jewellery product detail
[**listProducts**](CatalogApi.md#listproducts) | **GET** /products | List jewellery products


# **getProductById**
> ProductDetail getProductById(productId)

Get jewellery product detail

Returns full product detail including category, metal, occasion, description, active variants with per-variant stock, averageRating, and reviews. Supports US-002. Public endpoint. Flagship demo SKU Tropical Earring must return price 1999 cents USD. 

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
> ProductListResponse listProducts(page, pageSize, q, category, metal, occasion, minPriceCents, maxPriceCents, sort)

List jewellery products

Paginated jewellery listing with optional text search, price range, category, metal, and occasion filters. Supports US-001 browse requirements. Public endpoint; no authentication required. Prices are integer minor units with ISO 4217 currency USD. 

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCatalogApi();
final int page = 56; // int | 1-based page number
final int pageSize = 56; // int | Items per page
final String q = Tropical; // String | Case-insensitive search against product name and searchable text
final JewelleryCategorySlug category = ; // JewelleryCategorySlug | Filter by jewellery category slug
final MetalTone metal = ; // MetalTone | Filter by metal tone
final Occasion occasion = ; // Occasion | Filter by occasion
final int minPriceCents = 1000; // int | Minimum display price in USD cents (inclusive)
final int maxPriceCents = 3000; // int | Maximum display price in USD cents (inclusive)
final String sort = sort_example; // String | Sort order for results

try {
    final response = api.listProducts(page, pageSize, q, category, metal, occasion, minPriceCents, maxPriceCents, sort);
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
 **q** | **String**| Case-insensitive search against product name and searchable text | [optional] 
 **category** | [**JewelleryCategorySlug**](.md)| Filter by jewellery category slug | [optional] 
 **metal** | [**MetalTone**](.md)| Filter by metal tone | [optional] 
 **occasion** | [**Occasion**](.md)| Filter by occasion | [optional] 
 **minPriceCents** | **int**| Minimum display price in USD cents (inclusive) | [optional] 
 **maxPriceCents** | **int**| Maximum display price in USD cents (inclusive) | [optional] 
 **sort** | **String**| Sort order for results | [optional] [default to 'newest']

### Return type

[**ProductListResponse**](ProductListResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

