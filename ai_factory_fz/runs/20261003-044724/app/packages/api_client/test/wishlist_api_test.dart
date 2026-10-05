import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for WishlistApi
void main() {
  final instance = ApiClient().getWishlistApi();

  group(WishlistApi, () {
    // Get signed-in wishlist
    //
    //Future<WishlistResponse> getWishlist() async
    test('test getWishlist', () async {
      // TODO
    });

    // Import local guest wishlist product IDs
    //
    //Future<WishlistResponse> importWishlist(ImportWishlistRequest importWishlistRequest) async
    test('test importWishlist', () async {
      // TODO
    });

    // Replace wishlist product IDs
    //
    //Future<WishlistResponse> replaceWishlist(ReplaceWishlistRequest replaceWishlistRequest) async
    test('test replaceWishlist', () async {
      // TODO
    });

  });
}
