import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/wishlist/data/guest_wishlist_storage.dart';
import '../../../support/fixed_auth_notifier.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_notifier.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_screen.dart';

void main() {
  testWidgets('shows empty wishlist then lists saved guest products', (
    tester,
  ) async {
    final guestStorage = InMemoryGuestWishlistStorage();
    final container = ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestWishlistStorageProvider.overrideWithValue(guestStorage),
        catalogRepositoryProvider.overrideWithValue(_FakeCatalogRepository()),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const WishlistScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('No saved favorites yet'), findsOneWidget);

    await container.read(wishlistNotifierProvider.notifier).toggle('seed-product-1');
    await tester.pumpAndSettle();

    expect(find.text('Citrus Hand Soap'), findsOneWidget);
  });
}

class InMemoryGuestWishlistStorage extends GuestWishlistStorage {
  InMemoryGuestWishlistStorage() : super(const _EmptySecureStorage());

  Set<String> ids = {};

  @override
  Future<Set<String>> readProductIds() async => ids;

  @override
  Future<void> writeProductIds(Set<String> productIds) async {
    ids = productIds;
  }
}

class _EmptySecureStorage extends FlutterSecureStorage {
  const _EmptySecureStorage() : super();
}

class _FakeCatalogRepository implements CatalogRepository {
  @override
  Future<List<CatalogCategoryModel>> listCategories() async => const [];

  @override
  Future<CatalogProductListResult> listProducts(ProductListQuery query) async {
    return CatalogProductListResult(
      items: const [
        CatalogProduct(
          id: 'seed-product-1',
          name: 'Citrus Hand Soap',
          categorySlug: 'personal-care',
          categoryName: 'Personal Care',
          imageUrl: 'https://example.com/soap.jpg',
          amountCents: 799,
          currencyCode: 'USD',
          isAvailable: true,
        ),
      ],
      total: 1,
    );
  }
}
