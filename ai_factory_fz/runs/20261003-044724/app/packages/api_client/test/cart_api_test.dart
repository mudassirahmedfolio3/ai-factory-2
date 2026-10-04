import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CartApi
void main() {
  final instance = ApiClient().getCartApi();

  group(CartApi, () {
    // Get signed-in user cart
    //
    //Future<CartResponse> getCart() async
    test('test getCart', () async {
      // TODO
    });

    // Merge guest cart lines into account cart
    //
    //Future<CartResponse> mergeCart(MergeCartRequest mergeCartRequest) async
    test('test mergeCart', () async {
      // TODO
    });

    // Replace cart items (full sync)
    //
    //Future<CartResponse> replaceCart(ReplaceCartRequest replaceCartRequest) async
    test('test replaceCart', () async {
      // TODO
    });

  });
}
