import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/mock_catalog_parser.dart';
import 'package:shopease_app/features/catalog/data/mock_catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/catalog_models.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/catalog_validator.dart';

/// Tests run with the package root (app/) as the working directory.
String _assetSource() => File(kMockCatalogAssetPath).readAsStringSync();

Map<String, dynamic> _assetJson() =>
    jsonDecode(_assetSource()) as Map<String, dynamic>;

List<String> _errorsAfter(void Function(Map<String, dynamic> json) mutate) {
  final json = _assetJson();
  mutate(json);
  return CatalogValidator.errorsFor(MockCatalog.fromJson(json));
}

Map<String, dynamic> _product(Map<String, dynamic> json, int index) =>
    (json['products'] as List)[index] as Map<String, dynamic>;

Map<String, dynamic> _variant(Map<String, dynamic> product, int index) =>
    (product['variants'] as List)[index] as Map<String, dynamic>;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('bundled assets/mock_catalog.json', () {
    late MockCatalog catalog;

    setUpAll(() => catalog = parseMockCatalog(_assetSource()));

    test('parses and validates against the MockCatalog contract', () {
      expect(catalog.catalogVersion, 1);
      expect(CatalogValidator.errorsFor(catalog), isEmpty);
    });

    test('holds 10 to 20 products covering every product type', () {
      expect(catalog.products.length, inInclusiveRange(10, 20));
      expect(
        catalog.products.map((p) => p.productType).toSet(),
        ProductType.values.toSet(),
      );
    });

    test('contains a multi-variant product (finish and color temperature)', () {
      final multi = catalog.products.where((p) {
        final names = {
          for (final v in p.variants) ...v.options.map((o) => o.name),
        };
        return p.variants.length > 1 &&
            names.contains('finish') &&
            names.contains('color_temperature');
      });
      expect(multi, isNotEmpty);
    });

    test('contains a product on sale with salePrice below price', () {
      final onSale = catalog.products
          .expand((p) => p.variants)
          .where((v) => v.isOnSale);
      expect(onSale, isNotEmpty);
      for (final v in onSale) {
        expect(v.salePrice!.amountMinor, lessThan(v.price.amountMinor));
      }
    });

    test('contains a low-stock product (1 to 5 units in total)', () {
      expect(
        catalog.products.where((p) => p.stockStatus == StockStatus.lowStock),
        isNotEmpty,
      );
    });

    test('contains a fully out-of-stock product', () {
      expect(
        catalog.products.where((p) => p.stockStatus == StockStatus.outOfStock),
        isNotEmpty,
      );
    });

    test('contains an out-of-stock variant inside a multi-variant product', () {
      expect(
        catalog.products.where(
          (p) =>
              p.hasMultipleVariants &&
              p.stockStatus != StockStatus.outOfStock &&
              p.variants.any((v) => v.stockQuantity == 0),
        ),
        isNotEmpty,
      );
    });

    test('images are bundled asset paths with alt text', () {
      final images = [
        for (final p in catalog.products) ...[
          ...p.images,
          ...p.variants.map((v) => v.image),
        ],
      ];
      for (final image in images) {
        expect(image.url, startsWith('assets/images/products/'));
        expect(image.altText.trim(), isNotEmpty);
      }
    });

    test('bulbs carry bulb specs; fixtures carry fixture specs', () {
      final bulb = catalog.products.firstWhere(
        (p) => p.productType == ProductType.bulb,
      );
      expect(bulb.specifications.wattageW, isNotNull);
      expect(bulb.specifications.lumens, isNotNull);
      expect(bulb.specifications.colorTemperatureK, isNotNull);
      expect(bulb.specifications.dimmable, isNotNull);
      expect(bulb.specifications.bulbType, isNotNull);
      expect(bulb.specifications.ipRating, isNull);

      final fixture = catalog.products.firstWhere(
        (p) => p.productType == ProductType.ceilingLight,
      );
      expect(fixture.specifications.material, isNotNull);
      expect(fixture.specifications.finish, isNotNull);
      expect(fixture.specifications.widthMm, isNotNull);
      expect(fixture.specifications.ipRating, isNotNull);
      expect(fixture.specifications.bulbType, isNull);
    });
  });

  group('CatalogValidator', () {
    test('flags duplicate SKUs', () {
      final errors = _errorsAfter((json) {
        _variant(_product(json, 1), 0)['sku'] = _variant(
          _product(json, 0),
          0,
        )['sku'];
      });
      expect(errors, contains(contains('duplicate SKU')));
    });

    test('flags a sale price that is not below the price', () {
      final errors = _errorsAfter((json) {
        _variant(_product(json, 0), 0)['salePrice'] = {
          'amountMinor': 12999,
          'currency': 'USD',
        };
      });
      expect(errors, contains(contains('salePrice: must be lower than price')));
    });

    test('flags zero or multiple default variants', () {
      final none = _errorsAfter((json) {
        _variant(_product(json, 0), 0)['isDefault'] = false;
      });
      expect(none, contains(contains('exactly one variant must be isDefault')));

      final two = _errorsAfter((json) {
        _variant(_product(json, 0), 1)['isDefault'] = true;
      });
      expect(two, contains(contains('exactly one variant must be isDefault')));
    });

    test('flags a defaultVariantId that does not match', () {
      final errors = _errorsAfter((json) {
        _product(json, 0)['defaultVariantId'] = 'var_999';
      });
      expect(errors, contains(contains('defaultVariantId')));
    });

    test('flags negative stock, bad currency, ip rating and kelvin', () {
      final errors = _errorsAfter((json) {
        final product = _product(json, 0);
        final variant = _variant(product, 0);
        variant['stockQuantity'] = -1;
        variant['price'] = {'amountMinor': 100, 'currency': 'EUR'};
        variant['salePrice'] = null;
        (product['specifications'] as Map)['ipRating'] = 'IPX';
        (product['specifications'] as Map)['colorTemperatureK'] = 500;
      });
      expect(errors, contains(contains('stockQuantity: must be >= 0')));
      expect(errors, contains(contains('currency: only USD')));
      expect(errors, contains(contains('ipRating')));
      expect(errors, contains(contains('colorTemperatureK')));
    });

    test('flags empty variants, bad slugs and duplicate option names', () {
      final errors = _errorsAfter((json) {
        _product(json, 1)['slug'] = 'Not A Slug';
        final options = _variant(_product(json, 0), 0)['options'] as List;
        options.add({'name': 'finish', 'value': 'Chrome'});
        _product(json, 2)['variants'] = <Object>[];
      });
      expect(errors, contains(contains('is not kebab-case')));
      expect(errors, contains(contains('duplicate option "finish"')));
      expect(errors, contains(contains('at least one variant is required')));
    });

    test('validate throws CatalogValidationException', () {
      final json = _assetJson();
      _product(json, 0)['defaultVariantId'] = 'var_999';
      expect(
        () => CatalogValidator.validate(MockCatalog.fromJson(json)),
        throwsA(isA<CatalogValidationException>()),
      );
    });
  });

  group('parseMockCatalog', () {
    test('rejects malformed JSON', () {
      expect(
        () => parseMockCatalog('{not json'),
        throwsA(isA<CatalogLoadException>()),
      );
    });

    test('rejects a non-object root', () {
      expect(
        () => parseMockCatalog('[]'),
        throwsA(isA<CatalogLoadException>()),
      );
    });

    test('rejects JSON that does not match the schema', () {
      final json = _assetJson();
      _variant(_product(json, 0), 0).remove('sku');
      expect(
        () => parseMockCatalog(jsonEncode(json)),
        throwsA(isA<CatalogLoadException>()),
      );
    });

    test('rejects JSON that breaks catalog invariants', () {
      final json = _assetJson();
      _product(json, 0)['defaultVariantId'] = 'var_999';
      expect(
        () => parseMockCatalog(jsonEncode(json)),
        throwsA(
          isA<CatalogLoadException>().having(
            (e) => e.cause,
            'cause',
            isA<CatalogValidationException>(),
          ),
        ),
      );
    });
  });

  group('MockCatalogRepository', () {
    test('loads the asset declared in pubspec through rootBundle', () async {
      final repository = MockCatalogRepository(
        loadSource: () => rootBundle.loadString(kMockCatalogAssetPath),
      );
      final catalog = await repository.load();
      expect(catalog.products, isNotEmpty);
    });

    test('loads and parses the source only once', () async {
      var loads = 0;
      final repository = MockCatalogRepository(
        loadSource: () async {
          loads++;
          return _assetSource();
        },
      );
      await repository.load();
      await repository.fetchProducts(page: 1, pageSize: 10);
      await repository.getProduct('prd_001');
      expect(loads, 1);
    });

    test('does not cache a failed load so Retry can succeed', () async {
      var fail = true;
      final repository = MockCatalogRepository(
        loadSource: () async => fail ? '{broken' : _assetSource(),
      );
      await expectLater(
        repository.load(),
        throwsA(isA<CatalogLoadException>()),
      );
      fail = false;
      expect((await repository.load()).products, isNotEmpty);
    });

    test('wraps asset read failures in CatalogLoadException', () async {
      final repository = MockCatalogRepository(
        loadSource: () async => throw FlutterError('Unable to load asset'),
      );
      await expectLater(
        repository.load(),
        throwsA(isA<CatalogLoadException>()),
      );
    });

    test('fetchProducts slices 1-based pages with total', () async {
      final repository = MockCatalogRepository(
        loadSource: () async => _assetSource(),
      );
      final total = (await repository.load()).products.length;

      final first = await repository.fetchProducts(page: 1, pageSize: 10);
      expect(first.items, hasLength(10));
      expect(first.total, total);
      expect(first.page, 1);
      expect(first.pageSize, 10);
      expect(first.items.first.id, 'prd_001');

      final second = await repository.fetchProducts(page: 2, pageSize: 10);
      expect(second.items, hasLength(total - 10));

      final beyond = await repository.fetchProducts(page: 5, pageSize: 10);
      expect(beyond.items, isEmpty);
      expect(beyond.total, total);
    });

    test('fetchProducts rejects out-of-range paging arguments', () async {
      final repository = MockCatalogRepository(
        loadSource: () async => _assetSource(),
      );
      expect(
        () => repository.fetchProducts(page: 0, pageSize: 10),
        throwsArgumentError,
      );
      expect(
        () => repository.fetchProducts(page: 1, pageSize: 0),
        throwsArgumentError,
      );
      expect(
        () => repository.fetchProducts(page: 1, pageSize: 101),
        throwsArgumentError,
      );
    });

    test('getProduct returns the product or throws not found', () async {
      final repository = MockCatalogRepository(
        loadSource: () async => _assetSource(),
      );
      final product = await repository.getProduct('prd_001');
      expect(product.name, 'Aria Dome Pendant');
      expect(product.defaultVariant.sku, 'ARIA-PND-BLK-2700');
      await expectLater(
        repository.getProduct('prd_missing'),
        throwsA(isA<ProductNotFoundException>()),
      );
    });
  });
}
