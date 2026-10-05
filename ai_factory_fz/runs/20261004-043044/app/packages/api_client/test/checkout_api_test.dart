import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CheckoutApi
void main() {
  final instance = ApiClient().getCheckoutApi();

  group(CheckoutApi, () {
    // Create order and reserve stock
    //
    //Future<CreateOrderResponse> createOrder(String idempotencyKey, CreateOrderRequest createOrderRequest, { String xGuestCartId }) async
    test('test createOrder', () async {
      // TODO
    });

    // Preview totals and shipping
    //
    //Future<CheckoutPreviewResponse> previewCheckout(CheckoutPreviewRequest checkoutPreviewRequest, { String xGuestCartId }) async
    test('test previewCheckout', () async {
      // TODO
    });

  });
}
