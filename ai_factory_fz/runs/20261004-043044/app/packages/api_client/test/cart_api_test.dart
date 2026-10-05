import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CartApi
void main() {
  final instance = ApiClient().getCartApi();

  group(CartApi, () {
    // Add cart line
    //
    //Future<CartResponse> addCartItem(AddCartItemRequest addCartItemRequest, { String xGuestCartId }) async
    test('test addCartItem', () async {
      // TODO
    });

    // Get cart
    //
    //Future<CartResponse> getCart({ String xGuestCartId }) async
    test('test getCart', () async {
      // TODO
    });

    // Merge guest cart after login
    //
    //Future<CartResponse> mergeGuestCart({ String xGuestCartId }) async
    test('test mergeGuestCart', () async {
      // TODO
    });

    // Remove line
    //
    //Future<CartResponse> removeCartItem(String itemId, { String xGuestCartId }) async
    test('test removeCartItem', () async {
      // TODO
    });

    // Update quantity
    //
    //Future<CartResponse> updateCartItem(String itemId, UpdateCartItemRequest updateCartItemRequest, { String xGuestCartId }) async
    test('test updateCartItem', () async {
      // TODO
    });

  });
}
