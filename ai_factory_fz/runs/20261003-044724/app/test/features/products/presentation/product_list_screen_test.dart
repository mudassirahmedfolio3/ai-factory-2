import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/utils/money_formatter.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';
import 'package:shopease_app/features/products/presentation/search_results_screen.dart';
import 'package:shopease_app/features/wishlist/presentation/wishlist_notifier.dart';

void main() {
  testWidgets('renders mock products after loading', (tester) async {
    final repository = _FakeCatalogRepository(products: _seedProducts);
    await tester.pumpWidget(_buildTestApp(repository));

    expect(find.text('Search'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpAndSettle();

    expect(find.text('4 products'), findsOneWidget);
    expect(find.text('Citrus Hand Soap'), findsOneWidget);
    expect(find.text('Aroma Candle'), findsOneWidget);
    expect(
      find.text(
        MoneyFormatter.formatMinorUnits(
          amountMinorUnits: 799,
          currencyCode: 'USD',
        ),
      ),
      findsOneWidget,
    );
    expect(find.textContaining('counter'), findsNothing);
  });

  testWidgets('applies search filter through ProductListNotifier', (
    tester,
  ) async {
    final repository = _FakeCatalogRepository(products: _seedProducts);
    await tester.pumpWidget(_buildTestApp(repository));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), 'candle');
    await tester.pumpAndSettle();
    expect(find.text('1 products'), findsOneWidget);
    expect(find.text('Aroma Candle'), findsOneWidget);
    expect(find.text('Citrus Hand Soap'), findsNothing);

    await tester.tap(find.byTooltip('Clear search'));
    await tester.pumpAndSettle();
    expect(find.text('4 products'), findsOneWidget);
  });

  testWidgets('shows error state and allows retry', (tester) async {
    final repository = _FlakyCatalogRepository(products: _seedProducts);
    await tester.pumpWidget(_buildTestApp(repository));
    await tester.pumpAndSettle();

    expect(
      find.text(
        'We are having trouble loading products right now. Please try again.',
      ),
      findsOneWidget,
    );
    expect(find.text('Try again'), findsOneWidget);

    repository.shouldFail = false;
    await tester.tap(find.text('Try again'));
    await tester.pumpAndSettle();

    expect(find.text('4 products'), findsOneWidget);
  });
}

Widget _buildTestApp(CatalogRepository repository) {
  return ProviderScope(
    overrides: [
      catalogRepositoryProvider.overrideWithValue(repository),
      wishlistNotifierProvider.overrideWith(_TestWishlistNotifier.new),
    ],
    child: MaterialApp(
      theme: AppTheme.lightTheme,
      home: const SearchResultsScreen(),
    ),
  );
}

class _TestWishlistNotifier extends WishlistNotifier {
  @override
  Future<Set<String>> build() async => {};
}

const _seedProducts = <CatalogProduct>[
  CatalogProduct(
    id: '1',
    name: 'Citrus Hand Soap',
    categorySlug: 'personal-care',
    categoryName: 'Personal Care',
    imageUrl: 'https://example.com/soap.jpg',
    amountCents: 799,
    currencyCode: 'USD',
    isAvailable: true,
  ),
  CatalogProduct(
    id: '2',
    name: 'Aroma Candle',
    categorySlug: 'home-lifestyle',
    categoryName: 'Home & Lifestyle',
    imageUrl: 'https://example.com/candle.jpg',
    amountCents: 2499,
    currencyCode: 'USD',
    isAvailable: true,
  ),
  CatalogProduct(
    id: '3',
    name: 'Hydrating Face Serum',
    categorySlug: 'personal-care',
    categoryName: 'Personal Care',
    imageUrl: 'https://example.com/serum.jpg',
    amountCents: 5299,
    currencyCode: 'USD',
    isAvailable: true,
  ),
  CatalogProduct(
    id: '4',
    name: 'Signature Celebration Hamper',
    categorySlug: 'gift-friendly',
    categoryName: 'Gift-Friendly Bestsellers',
    imageUrl: 'https://example.com/hamper.jpg',
    amountCents: 14999,
    currencyCode: 'USD',
    isAvailable: true,
  ),
];

class _FakeCatalogRepository implements CatalogRepository {
  _FakeCatalogRepository({required this.products});

  final List<CatalogProduct> products;

  @override
  Future<List<CatalogCategoryModel>> listCategories() async => const [];

  @override
  Future<CatalogProductListResult> listProducts(ProductListQuery query) async {
    var filtered = [...products];
    final normalizedQuery = query.q?.trim().toLowerCase() ?? '';
    if (normalizedQuery.isNotEmpty) {
      filtered = filtered
          .where((p) => p.name.toLowerCase().contains(normalizedQuery))
          .toList(growable: false);
    }
    return CatalogProductListResult(items: filtered, total: filtered.length);
  }
}

class _FlakyCatalogRepository implements CatalogRepository {
  _FlakyCatalogRepository({required this.products});

  final List<CatalogProduct> products;
  bool shouldFail = true;

  @override
  Future<List<CatalogCategoryModel>> listCategories() async => const [];

  @override
  Future<CatalogProductListResult> listProducts(ProductListQuery query) async {
    if (shouldFail) {
      throw Exception('Failed to load');
    }
    return CatalogProductListResult(items: products, total: products.length);
  }
}
