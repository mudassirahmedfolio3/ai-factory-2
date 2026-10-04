import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/money/money.dart';
import 'package:shopease_app/features/catalog/data/catalog_providers.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/product_detail.dart';
import 'package:shopease_app/features/catalog/domain/product_page.dart';

class _FakeRepository implements CatalogRepository {
  _FakeRepository(this.products, {this.fail = false});

  final List<ProductDetail> products;
  bool fail;

  @override
  Future<ProductPage> listProducts({int page = 1, int pageSize = 20}) async {
    if (fail) throw const CatalogueLoadException('boom');
    return ProductPage(
      items: [for (final p in products) p.toSummary()],
      total: products.length,
      page: page,
      pageSize: pageSize,
    );
  }

  @override
  Future<ProductDetail> getProduct(String productId) async =>
      products.firstWhere(
        (p) => p.id == productId,
        orElse: () => throw ProductNotFoundException(productId),
      );
}

ProductDetail _product(String id, String name, int pence, int stock) =>
    ProductDetail(
      id: id,
      name: name,
      description: 'About $name',
      price: Money.gbp(pence),
      imageUrl: null,
      thumbnailUrl: null,
      inStock: stock > 0,
      stockQuantity: stock,
      defaultVariantId: 'v-$id',
    );

Widget _app(CatalogRepository repo) => ProviderScope(
  overrides: [catalogRepositoryProvider.overrideWithValue(repo)],
  child: const SimpleShopApp(),
);

void main() {
  testWidgets('launches onto the product list without sign-in', (tester) async {
    await tester.pumpWidget(
      _app(
        _FakeRepository([
          _product('1', 'Mug', 1299, 5),
          _product('2', 'Board', 2450, 0),
        ]),
      ),
    );
    expect(find.bySemanticsLabel('Loading'), findsOneWidget);
    await tester.pumpAndSettle();

    expect(find.text('Simple Shop'), findsOneWidget);
    expect(find.text('Mug'), findsOneWidget);
    expect(find.text('£12.99'), findsOneWidget);
    expect(find.text('£24.50'), findsOneWidget);
    expect(find.text('In stock'), findsOneWidget);
    expect(find.text('Out of stock'), findsOneWidget);
    expect(find.textContaining('Sign in'), findsNothing);
  });

  testWidgets('shows the empty state when there are no products', (
    tester,
  ) async {
    await tester.pumpWidget(_app(_FakeRepository(const [])));
    await tester.pumpAndSettle();
    expect(find.text('No products available'), findsOneWidget);
  });

  testWidgets('shows an error with retry that reloads', (tester) async {
    final repo = _FakeRepository([_product('1', 'Mug', 1299, 5)], fail: true);
    await tester.pumpWidget(_app(repo));
    await tester.pumpAndSettle();
    expect(find.text('Products could not be loaded.'), findsOneWidget);

    repo.fail = false;
    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();
    expect(find.text('Mug'), findsOneWidget);
  });

  testWidgets('runs end-to-end on the bundled mock catalogue', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: SimpleShopApp()));
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 200)),
    );
    await tester.pumpAndSettle();
    expect(find.text('Ceramic Coffee Mug'), findsOneWidget);
    expect(find.text('£12.99'), findsOneWidget);
  });
}
