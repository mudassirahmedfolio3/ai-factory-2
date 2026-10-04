import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/mock_catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';

Map<String, dynamic> _entry(
  String id, {
  Object? amount = 1299,
  int stock = 3,
}) => {
  'id': id,
  'name': 'Product $id',
  'description': 'Description $id',
  'price': {'amountMinor': amount, 'currency': 'GBP'},
  'imageUrl': null,
  'thumbnailUrl': null,
  'inStock': true,
  'stockQuantity': stock,
  'defaultVariantId': 'variant-$id',
};

MockCatalogRepository _repoFrom(List<Object?> products) =>
    MockCatalogRepository(
      source: () async => jsonEncode({'products': products}),
    );

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('bundled catalogue asset', () {
    late MockCatalogRepository repo;
    late List<Object?> rawProducts;

    setUp(() {
      // Read the same file that is bundled via pubspec.yaml.
      final raw = File(MockCatalogRepository.assetPath).readAsStringSync();
      rawProducts =
          (jsonDecode(raw) as Map<String, dynamic>)['products']
              as List<Object?>;
      repo = MockCatalogRepository(source: () async => raw);
    });

    test('is declared as an asset and loads through rootBundle', () async {
      final bundled = MockCatalogRepository();
      final page = await bundled.listProducts(pageSize: 100);
      expect(page.total, greaterThanOrEqualTo(10));
    });

    test('contains 10-20 products and every entry parses', () async {
      final all = await repo.loadAll();
      expect(all.length, inInclusiveRange(10, 20));
      expect(all.length, rawProducts.length, reason: 'no entry was skipped');
    });

    test('prices are integer pence in GBP (no floats in the data)', () async {
      for (final entry in rawProducts.cast<Map<String, dynamic>>()) {
        final price = entry['price'] as Map<String, dynamic>;
        expect(price['amountMinor'], isA<int>(), reason: '${entry['id']}');
        expect(price['currency'], 'GBP');
      }
    });

    test('includes out-of-stock and no-image products', () async {
      final all = await repo.loadAll();
      expect(all.where((p) => p.stockQuantity == 0 && !p.inStock), isNotEmpty);
      expect(all.where((p) => p.imageUrl == null), isNotEmpty);
      for (final p in all) {
        expect(p.inStock, p.stockQuantity > 0);
      }
    });

    test('ids are unique', () async {
      final all = await repo.loadAll();
      expect(all.map((p) => p.id).toSet().length, all.length);
    });
  });

  group('listProducts', () {
    final repo = _repoFrom([for (var i = 1; i <= 25; i++) _entry('p$i')]);

    test('returns the first page with total', () async {
      final page = await repo.listProducts(page: 1, pageSize: 20);
      expect(page.items.length, 20);
      expect(page.total, 25);
      expect(page.page, 1);
      expect(page.pageSize, 20);
      expect(page.items.first.id, 'p1');
      expect(page.hasMore, isTrue);
    });

    test('returns the remainder on the last page', () async {
      final page = await repo.listProducts(page: 2, pageSize: 20);
      expect(page.items.map((p) => p.id), ['p21', 'p22', 'p23', 'p24', 'p25']);
      expect(page.hasMore, isFalse);
    });

    test('returns an empty page beyond the end', () async {
      final page = await repo.listProducts(page: 5, pageSize: 20);
      expect(page.items, isEmpty);
      expect(page.total, 25);
    });

    test('validates page and pageSize like the API', () async {
      expect(() => repo.listProducts(page: 0), throwsArgumentError);
      expect(() => repo.listProducts(pageSize: 0), throwsArgumentError);
      expect(() => repo.listProducts(pageSize: 101), throwsArgumentError);
    });

    test('parses the source only once', () async {
      var loads = 0;
      final counting = MockCatalogRepository(
        source: () async {
          loads++;
          return jsonEncode({
            'products': [_entry('a')],
          });
        },
      );
      await counting.listProducts();
      await counting.getProduct('a');
      await counting.listProducts(page: 2);
      expect(loads, 1);
    });
  });

  group('getProduct', () {
    final repo = _repoFrom([_entry('a'), _entry('b', stock: 0)]);

    test('returns the matching product detail', () async {
      final product = await repo.getProduct('b');
      expect(product.name, 'Product b');
      expect(product.description, 'Description b');
      expect(product.defaultVariantId, 'variant-b');
      expect(product.inStock, isFalse);
    });

    test('throws ProductNotFoundException for unknown ids', () async {
      expect(
        () => repo.getProduct('missing'),
        throwsA(isA<ProductNotFoundException>()),
      );
    });
  });

  group('defensive parsing', () {
    test('skips malformed, float, negative and duplicate entries', () async {
      final repo = _repoFrom([
        _entry('ok'),
        'not an object',
        _entry('float', amount: 12.99),
        _entry('negative-price', amount: -1),
        _entry('negative-stock', stock: -2),
        {
          ..._entry('eur'),
          'price': {'amountMinor': 100, 'currency': 'EUR'},
        },
        {..._entry('no-name'), 'name': ''},
        _entry('ok'),
      ]);
      final all = await repo.loadAll();
      expect(all.map((p) => p.id), ['ok']);
    });

    test('derives inStock from stockQuantity, ignoring the raw flag', () {
      final product = MockCatalogRepository.parseEntry({
        ..._entry('x', stock: 0),
        'inStock': true,
      });
      expect(product!.inStock, isFalse);
    });

    test('treats blank image urls as missing', () {
      final product = MockCatalogRepository.parseEntry({
        ..._entry('x'),
        'imageUrl': '  ',
      });
      expect(product!.imageUrl, isNull);
    });

    test(
      'invalid JSON raises CatalogueLoadException and allows retry',
      () async {
        var attempt = 0;
        final repo = MockCatalogRepository(
          source: () async {
            attempt++;
            return attempt == 1
                ? '{not json'
                : jsonEncode({
                    'products': [_entry('a')],
                  });
          },
        );
        await expectLater(
          repo.listProducts(),
          throwsA(isA<CatalogueLoadException>()),
        );
        final page = await repo.listProducts();
        expect(page.total, 1);
      },
    );
  });
}
