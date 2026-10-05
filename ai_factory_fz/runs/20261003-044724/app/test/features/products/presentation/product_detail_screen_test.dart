import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/utils/money_formatter.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import '../../../support/fixed_auth_notifier.dart';
import 'package:shopease_app/features/cart/presentation/cart_controller.dart';
import 'package:shopease_app/features/products/data/product_detail_repository.dart';
import 'package:shopease_app/features/products/domain/product_detail_models.dart';
import 'package:shopease_app/features/products/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_notifier.dart';

void main() {
  testWidgets('renders product detail with rating and reviews', (tester) async {
    final repository = _FakeProductDetailRepository(
      detail: _inStockDetail,
      reviews: _reviews,
    );

    await tester.pumpWidget(
      _buildApp(repository: repository, productId: _inStockDetail.id),
    );

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpAndSettle();

    expect(find.text('Product detail'), findsOneWidget);
    expect(find.text('Citrus Hand Soap'), findsOneWidget);
    final expectedPrice = MoneyFormatter.formatMinorUnits(
      amountMinorUnits: 799,
      currencyCode: 'USD',
    );
    expect(find.text(expectedPrice), findsOneWidget);
    expect(find.textContaining('cents'), findsNothing);
    // US-005: shopper copy must avoid tax/commerce jargon on the detail path.
    expect(find.textContaining('Tax-exclusive'), findsNothing);
    expect(find.textContaining('catalog price'), findsNothing);
    expect(find.text('In stock'), findsOneWidget);
    expect(find.text('4.5 (2)'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Fresh scent and non-drying formula. Great for daily use.'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(
      find.text('Fresh scent and non-drying formula. Great for daily use.'),
      findsOneWidget,
    );
    await tester.scrollUntilVisible(
      find.text('Add to cart'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Add to cart'), findsOneWidget);
    expect(
      tester.widget<ElevatedButton>(find.byType(ElevatedButton)).onPressed,
      isNotNull,
    );
  });

  testWidgets('adds available product to in-memory guest cart with unit price', (
    tester,
  ) async {
    final repository = _FakeProductDetailRepository(
      detail: _inStockDetail,
      reviews: _reviews,
    );
    final container = ProviderContainer(
      overrides: [
        productDetailRepositoryProvider.overrideWithValue(repository),
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestCartStorageProvider.overrideWithValue(
          InMemoryGuestCartLocalRepository(),
        ),
      ],
    );
    addTearDown(container.dispose);
    await container.read(cartControllerProvider.future);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: ProductDetailScreen(productId: _inStockDetail.id),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(
      find.text('Add to cart'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text('Add to cart'));
    await tester.pumpAndSettle();

    final cart = container.read(cartControllerProvider).value!;
    expect(cart.lines, hasLength(1));
    expect(cart.lines.first.productId, _inStockDetail.id);
    expect(cart.lines.first.unitPriceCents, 799);
    expect(cart.lines.first.currencyCode, 'USD');
    expect(cart.itemCount, 1);
  });

  testWidgets('disables add to cart for out-of-stock variant', (tester) async {
    final repository = _FakeProductDetailRepository(
      detail: _outOfStockDetail,
      reviews: const <ProductReviewModel>[],
    );

    await tester.pumpWidget(
      _buildApp(repository: repository, productId: _outOfStockDetail.id),
    );
    await tester.pumpAndSettle();

    expect(find.text('Out of stock'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('No reviews yet'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('No reviews yet'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Add to cart'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    final addToCartButton = tester.widget<ElevatedButton>(
      find.widgetWithText(ElevatedButton, 'Add to cart'),
    );
    expect(addToCartButton.onPressed, isNull);
  });

  testWidgets('shows error and retries successfully', (tester) async {
    final repository = _FlakyProductDetailRepository(
      detail: _inStockDetail,
      reviews: _reviews,
    );

    await tester.pumpWidget(
      _buildApp(repository: repository, productId: _inStockDetail.id),
    );
    await tester.pumpAndSettle();

    expect(
      find.text('We could not load this product right now. Please try again.'),
      findsOneWidget,
    );

    repository.shouldThrow = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();

    expect(find.text('Citrus Hand Soap'), findsOneWidget);
  });
}

Widget _buildApp({
  required ProductDetailRepository repository,
  required String productId,
}) {
  return ProviderScope(
    overrides: [
      productDetailRepositoryProvider.overrideWithValue(repository),
      authNotifierProvider.overrideWith(GuestAuthNotifier.new),
      wishlistNotifierProvider.overrideWith(_EmptyWishlistNotifier.new),
      guestCartStorageProvider.overrideWithValue(
        InMemoryGuestCartLocalRepository(),
      ),
    ],
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: ProductDetailScreen(productId: productId),
    ),
  );
}

const _inStockDetail = ProductDetailModel(
  id: 'seed-product-1',
  name: 'Citrus Hand Soap',
  description: 'A gentle citrus hand soap for everyday use, with a clean rinse and bright scent.',
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
  reviewCount: 2,
);

const _outOfStockDetail = ProductDetailModel(
  id: 'seed-product-10',
  name: 'Premium Scented Diffuser',
  description: 'Premium diffuser with a refined scent profile for living spaces and offices.',
  categorySlug: 'home-lifestyle',
  images: <ProductImageModel>[
    ProductImageModel(
      id: 'img-1',
      url: 'https://example.com/diffuser.jpg',
      altText: 'Premium diffuser',
      position: 0,
    ),
  ],
  variants: <ProductVariantModel>[
    ProductVariantModel(
      id: 'var-1',
      sku: 'SHO-DIF-XL',
      name: 'XL',
      amountCents: 9999,
      currencyCode: 'USD',
      inventoryCount: 0,
      isAvailable: false,
    ),
  ],
  isAvailable: false,
  averageRating: 4.2,
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
  ProductReviewModel(
    id: 'review-2',
    authorName: 'Oliver',
    rating: 4,
    comment: 'Nice quality and value. Pump is smooth and easy to use.',
    createdAt: DateTime(2026, 8, 10),
  ),
];

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

class _FlakyProductDetailRepository implements ProductDetailRepository {
  _FlakyProductDetailRepository({required this.detail, required this.reviews});

  final ProductDetailModel detail;
  final List<ProductReviewModel> reviews;
  bool shouldThrow = true;

  @override
  Future<ProductDetailModel?> fetchProductDetail(String productId) async {
    if (shouldThrow) {
      throw Exception('Failed to fetch detail');
    }
    return detail;
  }

  @override
  Future<List<ProductReviewModel>> fetchReviews(String productId) async {
    return reviews;
  }
}
