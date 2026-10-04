# api_client.api.ReviewsApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**listProductReviews**](ReviewsApi.md#listproductreviews) | **GET** /products/{productId}/reviews | List paginated reviews for a product


# **listProductReviews**
> ReviewListResponse listProductReviews(productId, page, pageSize)

List paginated reviews for a product

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getReviewsApi();
final String productId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | 
final int page = 56; // int | 
final int pageSize = 56; // int | 

try {
    final response = api.listProductReviews(productId, page, pageSize);
    print(response);
} on DioException catch (e) {
    print('Exception when calling ReviewsApi->listProductReviews: $e\n');
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

