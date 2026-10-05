# api_client.api.UsersApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**deleteAccount**](UsersApi.md#deleteaccount) | **DELETE** /users/me | Delete the signed-in account


# **deleteAccount**
> deleteAccount()

Delete the signed-in account

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getUsersApi();

try {
    api.deleteAccount();
} on DioException catch (e) {
    print('Exception when calling UsersApi->deleteAccount: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

void (empty response body)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

