# api_client.api.CheckoutApi

## Load the API package
```dart
import 'package:api_client/api.dart';
```

All URIs are relative to *http://10.0.2.2:3000/api/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createCheckoutQuote**](CheckoutApi.md#createcheckoutquote) | **POST** /checkout/quote | Compute shipping, tax, coupon, and totals


# **createCheckoutQuote**
> CheckoutQuoteResponse createCheckoutQuote(checkoutQuoteRequest)

Compute shipping, tax, coupon, and totals

### Example
```dart
import 'package:api_client/api.dart';

final api = ApiClient().getCheckoutApi();
final CheckoutQuoteRequest checkoutQuoteRequest = ; // CheckoutQuoteRequest | 

try {
    final response = api.createCheckoutQuote(checkoutQuoteRequest);
    print(response);
} on DioException catch (e) {
    print('Exception when calling CheckoutApi->createCheckoutQuote: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **checkoutQuoteRequest** | [**CheckoutQuoteRequest**](CheckoutQuoteRequest.md)|  | 

### Return type

[**CheckoutQuoteResponse**](CheckoutQuoteResponse.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

