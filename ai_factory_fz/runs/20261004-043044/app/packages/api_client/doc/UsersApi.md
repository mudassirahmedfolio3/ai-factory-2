# api_client.api.UsersApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**deleteCurrentUser**](UsersApi.md#deletecurrentuser) | **DELETE** /users/me | Delete account
[**getCurrentUser**](UsersApi.md#getcurrentuser) | **GET** /users/me | Current profile


# **deleteCurrentUser**
> deleteCurrentUser()

Delete account

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getUsersApi();

try {
    api.deleteCurrentUser();
} on DioException catch (e) {
    print('Exception when calling UsersApi->deleteCurrentUser: $e\n');
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

# **getCurrentUser**
> UserProfile getCurrentUser()

Current profile

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getUsersApi();

try {
    final response = api.getCurrentUser();
    print(response);
} on DioException catch (e) {
    print('Exception when calling UsersApi->getCurrentUser: $e\n');
}
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**UserProfile**](UserProfile.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

