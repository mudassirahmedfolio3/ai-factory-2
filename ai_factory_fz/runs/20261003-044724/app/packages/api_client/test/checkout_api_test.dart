import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CheckoutApi
void main() {
  final instance = ApiClient().getCheckoutApi();

  group(CheckoutApi, () {
    // Compute shipping, tax, coupon, and totals
    //
    //Future<CheckoutQuoteResponse> createCheckoutQuote(CheckoutQuoteRequest checkoutQuoteRequest) async
    test('test createCheckoutQuote', () async {
      // TODO
    });

  });
}
