# api_client.api.CategoriesApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**listCategories**](CategoriesApi.md#listcategories) | **GET** /categories | List all catalog categories


# **listCategories**
> CategoryListResponse listCategories()

List all catalog categories

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCategoriesApi();

try {
    final response = api.listCategories();
    print(response);
} on DioException catch (e) {
    print('Exception when calling CategoriesApi->listCategories: $e\n');
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

