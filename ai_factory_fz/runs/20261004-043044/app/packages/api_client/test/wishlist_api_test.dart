import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for WishlistApi
void main() {
  final instance = ApiClient().getWishlistApi();

  group(WishlistApi, () {
    // Add wishlist item
    //
    //Future<WishlistItem> addWishlistItem(AddWishlistItemRequest addWishlistItemRequest) async
    test('test addWishlistItem', () async {
      // TODO
    });

    // List wishlist
    //
    //Future<WishlistListResponse> listWishlist({ int page, int pageSize }) async
    test('test listWishlist', () async {
      // TODO
    });

    // Remove wishlist item
    //
    //Future removeWishlistItem(String productId) async
    test('test removeWishlistItem', () async {
      // TODO
    });

  });
}
