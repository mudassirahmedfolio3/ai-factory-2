import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import '../../support/fixed_auth_notifier.dart';
import 'package:shopease_app/features/cart/presentation/cart_controller.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';
import 'package:shopease_app/features/products/data/product_detail_repository.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';
import 'package:shopease_app/features/products/domain/product_detail_models.dart';
import 'package:shopease_app/features/products/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/products/presentation/search_results_screen.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_notifier.dart';

void main() {
  testWidgets(
    'guest can browse detail and keep cart across screens without auth',
    (tester) async {
      final catalogRepository = _FakeCatalogRepository(products: _seedProducts);
      final detailRepository = _FakeProductDetailRepository(
        detail: _detail,
        reviews: _reviews,
      );
      final container = ProviderContainer(
        overrides: [
          catalogRepositoryProvider.overrideWithValue(catalogRepository),
          productDetailRepositoryProvider.overrideWithValue(detailRepository),
          wishlistNotifierProvider.overrideWith(_EmptyWishlistNotifier.new),
          authNotifierProvider.overrideWith(GuestAuthNotifier.new),
          guestCartStorageProvider.overrideWithValue(
            InMemoryGuestCartLocalRepository(),
          ),
        ],
      );
      addTearDown(container.dispose);

      final router = GoRouter(
        initialLocation: SearchResultsScreen.routePath,
        routes: [
          GoRoute(
            path: SearchResultsScreen.routePath,
            builder: (context, state) => const SearchResultsScreen(),
          ),
          GoRoute(
            path: ProductDetailScreen.routePath,
            builder: (context, state) {
              final productId = state.pathParameters['productId'] ?? '';
              return ProductDetailScreen(productId: productId);
            },
          ),
          GoRoute(
            path: CartScreen.routePath,
            builder: (context, state) => const CartScreen(),
          ),
        ],
      );

      await tester.pumpWidget(
        UncontrolledProviderScope(
          container: container,
          child: MaterialApp.router(
            theme: AppTheme.lightTheme,
            routerConfig: router,
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Search'), findsOneWidget);
      expect(find.textContaining('Sign in'), findsNothing);
      expect(find.textContaining('Register'), findsNothing);
      expect(find.textContaining('Login'), findsNothing);

      await tester.tap(find.text('Citrus Hand Soap'));
      await tester.pumpAndSettle();

      expect(find.text('Product detail'), findsOneWidget);
      expect(find.textContaining('Sign in'), findsNothing);

      final addToCart = find.widgetWithText(ElevatedButton, 'Add to cart');
      await tester.scrollUntilVisible(
        addToCart,
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      final addButton = tester.widget<ElevatedButton>(addToCart);
      expect(addButton.onPressed, isNotNull);
      addButton.onPressed!();
      await tester.pumpAndSettle();

      expect(container.read(cartControllerProvider).value!.itemCount, 1);

      await tester.tap(find.byTooltip('Open cart'));
      await tester.pumpAndSettle();

      expect(find.text('Your cart'), findsOneWidget);
      expect(find.text('Citrus Hand Soap'), findsOneWidget);
      expect(find.text('Sign in to sync cart'), findsOneWidget);
      expect(find.textContaining('password'), findsNothing);

      router.pop();
      await tester.pumpAndSettle();
      expect(find.text('Product detail'), findsOneWidget);
      expect(container.read(cartControllerProvider).value!.itemCount, 1);

      await tester.tap(find.byTooltip('Open cart'));
      await tester.pumpAndSettle();
      expect(find.text('Citrus Hand Soap'), findsOneWidget);
      expect(container.read(cartControllerProvider).value!.lines.first.unitPriceCents, 799);
    },
  );
}

const _seedProducts = <CatalogProduct>[
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
];

const _detail = ProductDetailModel(
  id: 'seed-product-1',
  name: 'Citrus Hand Soap',
  description: 'A gentle citrus hand soap for everyday use.',
  categorySlug: 'personal-care',
  images: <ProductImageModel>[
    ProductImageModel(
      id: 'img-1',
      url: 'https://example.com/soap.jpg',
      altText: 'Citrus hand soap bottle',
      position: 0,
    ),
  ],
  variants: <ProductVariantModel>[
    ProductVariantModel(
      id: 'var-1',
      sku: 'SHO-SOAP-300',
      name: '300 ml',
      amountCents: 799,
      currencyCode: 'USD',
      inventoryCount: 12,
      isAvailable: true,
    ),
  ],
  isAvailable: true,
  averageRating: 4.5,
  reviewCount: 1,
);

final _reviews = <ProductReviewModel>[
  ProductReviewModel(
    id: 'review-1',
    authorName: 'Maya',
    rating: 5,
    comment: 'Fresh scent and non-drying formula. Great for daily use.',
    createdAt: DateTime(2026, 8, 21),
  ),
];

class _FakeCatalogRepository implements CatalogRepository {
  _FakeCatalogRepository({required this.products});

  final List<CatalogProduct> products;

  @override
  Future<List<CatalogCategoryModel>> listCategories() async => const [];

  @override
  Future<CatalogProductListResult> listProducts(ProductListQuery query) async {
    return CatalogProductListResult(items: products, total: products.length);
  }
}

class _EmptyWishlistNotifier extends WishlistNotifier {
  @override
  Future<Set<String>> build() async => {};
}

class _FakeProductDetailRepository implements ProductDetailRepository {
  _FakeProductDetailRepository({required this.detail, required this.reviews});

  final ProductDetailModel detail;
  final List<ProductReviewModel> reviews;

  @override
  Future<ProductDetailModel?> fetchProductDetail(String productId) async {
    return detail;
  }

  @override
  Future<List<ProductReviewModel>> fetchReviews(String productId) async {
    return reviews;
  }
}
