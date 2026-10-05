import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/wishlist/data/guest_wishlist_storage.dart';

void main() {
  test('guest wishlist storage key is stable', () {
    expect(GuestWishlistStorage.storageKey, 'guest_wishlist_product_ids');
  });
}
