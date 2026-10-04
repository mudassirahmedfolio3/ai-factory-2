import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';

void main() {
  const products = <CatalogProduct>[
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

  test('category filter keeps only matching category slug', () async {
    final repository = _FakeCatalogRepository(products: products);
    final result = await repository.listProducts(
      const ProductListQuery(category: 'personal-care'),
    );
    expect(result.items.map((p) => p.id).toSet(), {'1', '3'});
  });

  test('search query matches product name', () async {
    final repository = _FakeCatalogRepository(products: products);
    final result = await repository.listProducts(
      const ProductListQuery(q: 'candle'),
    );
    expect(result.items, hasLength(1));
    expect(result.items.first.name, 'Aroma Candle');
  });

  test('price sort orders by integer cents ascending', () async {
    final repository = _FakeCatalogRepository(products: products);
    final result = await repository.listProducts(
      const ProductListQuery(sort: ProductListSort.priceAsc),
    );
    expect(result.items.map((p) => p.amountCents), [799, 2499, 5299, 14999]);
  });

  test('clearing filters restores full catalog', () async {
    final repository = _FakeCatalogRepository(products: products);
    final filtered = await repository.listProducts(
      const ProductListQuery(
        q: 'candle',
        category: 'home-lifestyle',
      ),
    );
    expect(filtered.items, hasLength(1));

    final cleared = await repository.listProducts(const ProductListQuery());
    expect(cleared.items, hasLength(products.length));
  });
}

class _FakeCatalogRepository implements CatalogRepository {
  _FakeCatalogRepository({required this.products});

  final List<CatalogProduct> products;

  @override
  Future<List<CatalogCategoryModel>> listCategories() async {
    return const [];
  }

  @override
  Future<CatalogProductListResult> listProducts(ProductListQuery query) async {
    var filtered = products.where((product) {
      final normalizedQuery = query.q?.trim().toLowerCase() ?? '';
      if (normalizedQuery.isNotEmpty &&
          !product.name.toLowerCase().contains(normalizedQuery)) {
        return false;
      }
      if (query.category != null && product.categorySlug != query.category) {
        return false;
      }
      if (query.brand != null && product.brand != query.brand) {
        return false;
      }
      if (query.minPriceCents != null &&
          product.amountCents < query.minPriceCents!) {
        return false;
      }
      if (query.maxPriceCents != null &&
          product.amountCents > query.maxPriceCents!) {
        return false;
      }
      if (query.availability != null &&
          product.availability != query.availability) {
        return false;
      }
      return true;
    }).toList(growable: false);

    switch (query.sort) {
      case ProductListSort.priceAsc:
        filtered = [...filtered]
          ..sort((a, b) => a.amountCents.compareTo(b.amountCents));
      case ProductListSort.priceDesc:
        filtered = [...filtered]
          ..sort((a, b) => b.amountCents.compareTo(a.amountCents));
      case ProductListSort.newest:
        filtered = [...filtered]..sort((a, b) => b.id.compareTo(a.id));
    }

    return CatalogProductListResult(items: filtered, total: filtered.length);
  }
}
