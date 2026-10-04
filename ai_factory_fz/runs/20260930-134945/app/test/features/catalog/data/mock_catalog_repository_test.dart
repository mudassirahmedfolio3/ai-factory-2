import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/mock_catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/product.dart';

/// In-memory bundle serving one string asset; counts loads.
class _FakeBundle extends CachingAssetBundle {
  _FakeBundle(this.content);

  String content;
  int loads = 0;
  bool fail = false;

  @override
  Future<ByteData> load(String key) async {
    loads++;
    if (fail) throw StateError('missing $key');
    final bytes = utf8.encode(content);
    return ByteData.sublistView(bytes);
  }

  @override
  Future<String> loadString(String key, {bool cache = true}) async {
    loads++;
    if (fail) throw StateError('missing $key');
    return content;
  }
}

Map<String, dynamic> _product(
  int n, {
  String? name,
  int priceMinor = 1000,
  int? salePriceMinor,
  int stockQuantity = 10,
  String? stockStatus,
  String currency = 'GBP',
}) => {
  'id': '00000000-0000-4000-8000-${n.toString().padLeft(12, '0')}',
  'sku': 'TST-$n',
  'name': name ?? 'Product $n',
  'brand': 'Brand',
  'category': {'id': 'c-1', 'slug': 'bulbs', 'name': 'Bulbs'},
  'priceMinor': priceMinor,
  'salePriceMinor': salePriceMinor,
  'currency': currency,
  'stockQuantity': stockQuantity,
  'stockStatus':
      stockStatus ??
      const {
        StockStatus.inStock: 'in_stock',
        StockStatus.lowStock: 'low_stock',
        StockStatus.outOfStock: 'out_of_stock',
      }[StockStatus.fromQuantity(stockQuantity)],
  'imageUrl': 'asset://images/products/p$n.webp',
  'imageAlt': 'Image of product $n',
  'description': 'Description $n',
  'specifications': <String, dynamic>{},
};

String _encode(List<Map<String, dynamic>> products) => jsonEncode(products);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('bundled catalog asset', () {
    late List<ProductDetail> products;

    setUpAll(() async {
      products = await MockCatalogRepository().loadAll();
    });

    test('contains 10-15 valid products', () {
      expect(products.length, inInclusiveRange(10, 15));
      for (final p in products) {
        expect(p.name.trim(), isNotEmpty);
        expect(p.priceMinor, greaterThan(0));
        expect(p.currency, 'GBP');
        expect(p.imageAlt.trim(), isNotEmpty);
        expect(p.description.trim(), isNotEmpty);
        expect(resolveAssetImagePath(p.imageUrl), startsWith('assets/images/'));
      }
    });

    test('covers all seven lighting categories', () {
      final slugs = products.map((p) => p.category.slug).toSet();
      expect(
        slugs,
        containsAll(<String>[
          'ceiling-lights',
          'pendant-lights',
          'wall-lights',
          'table-floor-lamps',
          'bulbs',
          'outdoor-lighting',
          'smart-lighting',
        ]),
      );
    });

    test('includes sale, low-stock and out-of-stock items', () {
      final sale = products.where((p) => p.salePriceMinor != null).toList();
      expect(sale.length, greaterThanOrEqualTo(2));
      for (final p in sale) {
        expect(p.salePriceMinor!, lessThan(p.priceMinor));
      }
      expect(
        products.where((p) => p.stockStatus == StockStatus.lowStock).length,
        greaterThanOrEqualTo(2),
      );
      expect(
        products.where((p) => p.stockStatus == StockStatus.outOfStock).length,
        greaterThanOrEqualTo(1),
      );
    });

    test('every product carries lighting specifications', () {
      for (final p in products) {
        final specs = p.specifications.toJson();
        expect(specs, isNotEmpty, reason: p.sku);
      }
    });

    test('ids and SKUs are unique and products are sorted by name', () {
      expect(products.map((p) => p.id).toSet().length, products.length);
      expect(products.map((p) => p.sku).toSet().length, products.length);
      final names = products.map((p) => p.name).toList();
      expect(names, [...names]..sort());
    });

    test('first page holds the whole seed with pageSize 50', () async {
      final page = await MockCatalogRepository().listProducts(pageSize: 50);
      expect(page.items.length, products.length);
      expect(page.total, products.length);
      expect(page.page, 1);
      expect(page.pageSize, 50);
    });
  });

  group('MockCatalogRepository', () {
    final seed = _encode([
      _product(3, name: 'Charlie'),
      _product(1, name: 'Alpha'),
      _product(2, name: 'Bravo', priceMinor: 2000, salePriceMinor: 1500),
      _product(4, name: 'Alpha'),
      _product(5, name: 'Echo', stockQuantity: 0),
    ]);

    test('sorts by name then id and paginates in memory', () async {
      final repo = MockCatalogRepository(bundle: _FakeBundle(seed));
      final first = await repo.listProducts(page: 1, pageSize: 2);
      expect(first.items.map((p) => p.sku), ['TST-1', 'TST-4']);
      expect(first.total, 5);
      final second = await repo.listProducts(page: 2, pageSize: 2);
      expect(second.items.map((p) => p.sku), ['TST-2', 'TST-3']);
      final third = await repo.listProducts(page: 3, pageSize: 2);
      expect(third.items.map((p) => p.sku), ['TST-5']);
      final beyond = await repo.listProducts(page: 9, pageSize: 2);
      expect(beyond.items, isEmpty);
      expect(beyond.total, 5);
    });

    test('defaults to page 1 and pageSize 20', () async {
      final repo = MockCatalogRepository(bundle: _FakeBundle(seed));
      final page = await repo.listProducts();
      expect(page.page, 1);
      expect(page.pageSize, defaultPageSize);
      expect(page.items.length, 5);
    });

    test('rejects out-of-range pagination', () async {
      final repo = MockCatalogRepository(bundle: _FakeBundle(seed));
      expect(() => repo.listProducts(page: 0), throwsArgumentError);
      expect(() => repo.listProducts(pageSize: 0), throwsArgumentError);
      expect(() => repo.listProducts(pageSize: 101), throwsArgumentError);
    });

    test('getProduct returns detail or throws not found', () async {
      final repo = MockCatalogRepository(bundle: _FakeBundle(seed));
      final p = await repo.getProduct('00000000-0000-4000-8000-000000000002');
      expect(p.name, 'Bravo');
      expect(p.effectivePriceMinor, 1500);
      await expectLater(
        repo.getProduct('unknown'),
        throwsA(isA<ProductNotFoundException>()),
      );
    });

    test('loads and parses the asset only once', () async {
      final bundle = _FakeBundle(seed);
      final repo = MockCatalogRepository(bundle: bundle);
      await repo.listProducts();
      await repo.getProduct('00000000-0000-4000-8000-000000000001');
      await repo.listProducts(page: 2, pageSize: 1);
      expect(bundle.loads, 1);
    });

    test('a failed load is not cached so retry can succeed', () async {
      final bundle = _FakeBundle(seed)..fail = true;
      final repo = MockCatalogRepository(bundle: bundle);
      await expectLater(
        repo.listProducts(),
        throwsA(isA<CatalogDataException>()),
      );
      bundle.fail = false;
      final page = await repo.listProducts();
      expect(page.total, 5);
    });
  });

  group('parseCatalog invariants', () {
    void expectInvalid(Object json) => expect(
      () => parseCatalog(json is String ? json : jsonEncode(json)),
      throwsA(isA<CatalogDataException>()),
    );

    test('accepts a valid seed', () {
      expect(parseCatalog(_encode([_product(1)])), hasLength(1));
    });

    test('rejects malformed JSON and wrong root', () {
      expectInvalid('not json');
      expectInvalid({'items': []});
      expectInvalid([1]);
    });

    test('rejects schema mismatches', () {
      expectInvalid([_product(1)..remove('priceMinor')]);
      expectInvalid([_product(1)..['unexpected'] = true]);
      expectInvalid([_product(1)..['priceMinor'] = 9.99]);
    });

    test('rejects non-positive price', () {
      expectInvalid([_product(1, priceMinor: 0)]);
    });

    test('rejects sale price not lower than price', () {
      expectInvalid([_product(1, priceMinor: 1000, salePriceMinor: 1000)]);
      expectInvalid([_product(1, priceMinor: 1000, salePriceMinor: 0)]);
    });

    test('rejects negative stock and mismatched stock status', () {
      expectInvalid([
        _product(1, stockQuantity: -1, stockStatus: 'out_of_stock'),
      ]);
      expectInvalid([_product(1, stockQuantity: 3, stockStatus: 'in_stock')]);
    });

    test('rejects non-GBP currency', () {
      expectInvalid([_product(1, currency: 'EUR')]);
    });

    test('rejects empty name and duplicate ids', () {
      expectInvalid([_product(1, name: ' ')]);
      expectInvalid([_product(1), _product(1)]);
    });
  });

  group('resolveAssetImagePath', () {
    test('maps asset:// URIs to bundled asset keys', () {
      expect(
        resolveAssetImagePath('asset://images/products/pendant-01.webp'),
        'assets/images/products/pendant-01.webp',
      );
      expect(resolveAssetImagePath('https://cdn.example.com/a.webp'), isNull);
      expect(resolveAssetImagePath('asset://'), isNull);
    });
  });

  test('catalogRepositoryProvider defaults to the mock and is overridable', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    expect(
      container.read(catalogRepositoryProvider),
      isA<MockCatalogRepository>(),
    );

    final fake = MockCatalogRepository(bundle: _FakeBundle('[]'));
    final overridden = ProviderContainer(
      overrides: [catalogRepositoryProvider.overrideWithValue(fake)],
    );
    addTearDown(overridden.dispose);
    expect(overridden.read(catalogRepositoryProvider), same(fake));
  });
}
