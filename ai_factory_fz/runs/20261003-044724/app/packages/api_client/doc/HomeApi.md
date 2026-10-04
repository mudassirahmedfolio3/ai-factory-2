# api_client.api.HomeApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getHome**](HomeApi.md#gethome) | **GET** /home | Merchandised home content


# **getHome**
> HomeResponse getHome()

Merchandised home content

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getHomeApi();

try {
    final response = api.getHome();
    print(response);
} on DioException catch (e) {
    print('Exception when calling HomeApi->getHome: $e\n');
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

