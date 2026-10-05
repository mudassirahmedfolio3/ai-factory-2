# api_client.api.SupportApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**submitSupportMessage**](SupportApi.md#submitsupportmessage) | **POST** /support/messages | Submit support form (simulated send)


# **submitSupportMessage**
> SupportMessageResponse submitSupportMessage(supportMessageRequest)

Submit support form (simulated send)

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getSupportApi();
final SupportMessageRequest supportMessageRequest = ; // SupportMessageRequest | 

try {
    final response = api.submitSupportMessage(supportMessageRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling SupportApi->submitSupportMessage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **supportMessageRequest** | [**SupportMessageRequest**](SupportMessageRequest.md)|  | 

### Return type

[**SupportMessageResponse**](SupportMessageResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

