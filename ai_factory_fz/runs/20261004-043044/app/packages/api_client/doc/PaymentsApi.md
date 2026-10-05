# api_client.api.PaymentsApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**confirmMockPayment**](PaymentsApi.md#confirmmockpayment) | **POST** /payments/mock/confirm | Confirm mock payment


# **confirmMockPayment**
> MockPaymentConfirmResponse confirmMockPayment(mockPaymentConfirmRequest)

Confirm mock payment

No card PAN/CVV fields accepted.

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getPaymentsApi();
final MockPaymentConfirmRequest mockPaymentConfirmRequest = ; // MockPaymentConfirmRequest | 

try {
    final response = api.confirmMockPayment(mockPaymentConfirmRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling PaymentsApi->confirmMockPayment: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **mockPaymentConfirmRequest** | [**MockPaymentConfirmRequest**](MockPaymentConfirmRequest.md)|  | 

### Return type

[**MockPaymentConfirmResponse**](MockPaymentConfirmResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

