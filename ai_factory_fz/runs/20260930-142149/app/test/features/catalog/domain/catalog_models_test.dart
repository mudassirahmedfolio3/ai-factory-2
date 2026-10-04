import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:json_annotation/json_annotation.dart';
import 'package:shopease_app/core/money/money.dart';
import 'package:shopease_app/features/catalog/domain/catalog_models.dart';

Map<String, dynamic> _variantJson({
  String id = 'var_1',
  String sku = 'SKU-1',
  bool isDefault = true,
  Object? salePrice,
  int stockQuantity = 10,
  Object? specificationOverrides,
}) => {
  'id': id,
  'sku': sku,
  'name': 'Matte Black / 2700K',
  'isDefault': isDefault,
  'options': [
    {'name': 'finish', 'value': 'Matte Black'},
    {'name': 'color_temperature', 'value': '2700K'},
  ],
  'price': {'amountMinor': 12999, 'currency': 'USD'},
  'salePrice': salePrice,
  'stockQuantity': stockQuantity,
  'image': {
    'url': 'assets/images/products/aria-pendant-black.webp',
    'altText': 'Aria pendant in matte black',
  },
  'specificationOverrides': specificationOverrides,
};

Map<String, dynamic> _productJson({List<Map<String, dynamic>>? variants}) => {
  'id': 'prd_1',
  'slug': 'aria-pendant',
  'name': 'Aria Dome Pendant',
  'brand': 'Lumora',
  'description': 'A dome pendant.',
  'productType': 'pendant',
  'category': {'id': 'cat_1', 'slug': 'pendants', 'name': 'Pendants'},
  'images': [
    {'url': 'assets/images/products/a.webp', 'altText': 'Aria pendant'},
  ],
  'ratingAverage': 4.6,
  'ratingCount': 128,
  'specifications': {
    'wattageW': 18,
    'lumens': 1400,
    'colorTemperatureK': 2700,
    'dimmable': true,
    'material': 'Spun aluminum',
    'finish': 'Matte Black',
    'ipRating': 'IP20',
  },
  'defaultVariantId': 'var_1',
  'variants':
      variants ??
      [
        _variantJson(),
        _variantJson(
          id: 'var_2',
          sku: 'SKU-2',
          isDefault: false,
          salePrice: {'amountMinor': 9999, 'currency': 'USD'},
          stockQuantity: 3,
          specificationOverrides: {'colorTemperatureK': 3000, 'lumens': 1450},
        ),
      ],
};

/// Round-trips through a real JSON string so nested toJson output is plain.
Map<String, dynamic> _roundTrip(Map<String, dynamic> json) =>
    jsonDecode(jsonEncode(json)) as Map<String, dynamic>;

/// Matches a checked json_serializable failure whose root cause is [T].
Matcher _checkedFailure<T>() => throwsA(
  isA<CheckedFromJsonException>().having(
    (e) => e.innerError,
    'innerError',
    isA<T>(),
  ),
);

void main() {
  group('StockStatus', () {
    test('is derived from quantity with a low-stock threshold of 5', () {
      expect(StockStatus.fromQuantity(0), StockStatus.outOfStock);
      expect(StockStatus.fromQuantity(1), StockStatus.lowStock);
      expect(StockStatus.fromQuantity(5), StockStatus.lowStock);
      expect(StockStatus.fromQuantity(6), StockStatus.inStock);
    });

    test('has customer-facing labels', () {
      expect(StockStatus.inStock.label, 'In stock');
      expect(StockStatus.lowStock.label, 'Low stock');
      expect(StockStatus.outOfStock.label, 'Out of stock');
    });
  });

  group('LightingSpecifications', () {
    test('absent fields parse as null (not applicable)', () {
      final specs = LightingSpecifications.fromJson({'wattageW': 9});
      expect(specs.wattageW, 9);
      expect(specs.material, isNull);
      expect(specs.ipRating, isNull);
      expect(specs.isEmpty, isFalse);
      expect(const LightingSpecifications().isEmpty, isTrue);
    });

    test('mergedWith lets non-null override fields win', () {
      const base = LightingSpecifications(
        wattageW: 18,
        lumens: 1400,
        colorTemperatureK: 2700,
        finish: 'Matte Black',
      );
      final merged = base.mergedWith(
        const LightingSpecifications(colorTemperatureK: 3000, lumens: 1450),
      );
      expect(merged.wattageW, 18);
      expect(merged.lumens, 1450);
      expect(merged.colorTemperatureK, 3000);
      expect(merged.finish, 'Matte Black');
      expect(base.mergedWith(null), base);
    });

    test('rejects keys outside the schema', () {
      expect(
        () => LightingSpecifications.fromJson({'beamAngle': 36}),
        _checkedFailure<UnrecognizedKeysException>(),
      );
    });
  });

  group('ProductVariant', () {
    test('parses integer-cent prices, nullable sale price and options', () {
      final variant = ProductVariant.fromJson(_variantJson());
      expect(variant.price, const Money.usd(12999));
      expect(variant.salePrice, isNull);
      expect(variant.isOnSale, isFalse);
      expect(variant.effectivePrice, const Money.usd(12999));
      expect(variant.optionValue('finish'), 'Matte Black');
      expect(variant.optionValue('wattage'), isNull);
      expect(variant.specificationOverrides, isNull);
      expect(variant.stockStatus, StockStatus.inStock);
    });

    test('effective price is the sale price when on sale', () {
      final variant = ProductVariant.fromJson(
        _variantJson(salePrice: {'amountMinor': 9999, 'currency': 'USD'}),
      );
      expect(variant.isOnSale, isTrue);
      expect(variant.effectivePrice, const Money.usd(9999));
    });

    test('round-trips through JSON unchanged', () {
      final json = _variantJson(
        salePrice: {'amountMinor': 9999, 'currency': 'USD'},
        specificationOverrides: {'colorTemperatureK': 3000},
      );
      final variant = ProductVariant.fromJson(json);
      expect(ProductVariant.fromJson(_roundTrip(variant.toJson())), variant);
      expect(_roundTrip(variant.toJson())['salePrice'], {
        'amountMinor': 9999,
        'currency': 'USD',
      });
    });

    test('requires salePrice and specificationOverrides keys (nullable)', () {
      final withoutSale = _variantJson()..remove('salePrice');
      expect(
        () => ProductVariant.fromJson(withoutSale),
        _checkedFailure<MissingRequiredKeysException>(),
      );
      final withoutOverrides = _variantJson()..remove('specificationOverrides');
      expect(
        () => ProductVariant.fromJson(withoutOverrides),
        _checkedFailure<MissingRequiredKeysException>(),
      );
    });

    test('rejects floating-point money', () {
      final json = _variantJson()
        ..['price'] = {'amountMinor': 129.99, 'currency': 'USD'};
      expect(
        () => ProductVariant.fromJson(json),
        _checkedFailure<FormatException>(),
      );
    });

    test('rejects a missing required field', () {
      final json = _variantJson()..remove('sku');
      expect(
        () => ProductVariant.fromJson(json),
        throwsA(isA<CheckedFromJsonException>()),
      );
    });
  });

  group('Product', () {
    test('parses all fields including enums, category and variants', () {
      final product = Product.fromJson(_productJson());
      expect(product.id, 'prd_1');
      expect(product.brand, 'Lumora');
      expect(product.productType, ProductType.pendant);
      expect(product.category.slug, 'pendants');
      expect(product.images.single.altText, 'Aria pendant');
      expect(product.ratingAverage, 4.6);
      expect(product.specifications.ipRating, 'IP20');
      expect(product.variants, hasLength(2));
      expect(product.hasMultipleVariants, isTrue);
    });

    test('round-trips through JSON unchanged', () {
      final product = Product.fromJson(_productJson());
      final encoded = _roundTrip(product.toJson());
      expect(Product.fromJson(encoded), product);
      expect(encoded['productType'], 'pendant');
    });

    test('serialises snake_case enum values', () {
      final json = _productJson()..['productType'] = 'smart_light';
      final product = Product.fromJson(json);
      expect(product.productType, ProductType.smartLight);
      expect(product.toJson()['productType'], 'smart_light');
    });

    test('rejects an unknown product type', () {
      final json = _productJson()..['productType'] = 'chandelier';
      expect(
        () => Product.fromJson(json),
        throwsA(isA<CheckedFromJsonException>()),
      );
    });

    test('accepts a null rating average', () {
      final json = _productJson()
        ..['ratingAverage'] = null
        ..['ratingCount'] = 0;
      expect(Product.fromJson(json).ratingAverage, isNull);
    });

    test('resolves default variant, stock and merged specifications', () {
      final product = Product.fromJson(_productJson());
      expect(product.defaultVariant.id, 'var_1');
      expect(product.variantById('var_2')?.sku, 'SKU-2');
      expect(product.variantById('nope'), isNull);
      expect(product.totalStock, 13);
      expect(product.stockStatus, StockStatus.inStock);

      final specs = product.specificationsFor(product.variantById('var_2')!);
      expect(specs.colorTemperatureK, 3000);
      expect(specs.lumens, 1450);
      expect(specs.wattageW, 18);
    });

    test('product is out of stock only when every variant is', () {
      final product = Product.fromJson(
        _productJson(
          variants: [
            _variantJson(stockQuantity: 0),
            _variantJson(
              id: 'var_2',
              sku: 'SKU-2',
              isDefault: false,
              stockQuantity: 0,
            ),
          ],
        ),
      );
      expect(product.stockStatus, StockStatus.outOfStock);
    });

    test('toSummary projects the default variant price and image', () {
      final json = _productJson()..['defaultVariantId'] = 'var_2';
      (json['variants'] as List)[0]['isDefault'] = false;
      (json['variants'] as List)[1]['isDefault'] = true;
      final summary = Product.fromJson(json).toSummary();
      expect(summary.id, 'prd_1');
      expect(summary.defaultVariantId, 'var_2');
      expect(summary.price, const Money.usd(12999));
      expect(summary.salePrice, const Money.usd(9999));
      expect(summary.effectivePrice, const Money.usd(9999));
      expect(summary.isOnSale, isTrue);
      expect(summary.stockStatus, StockStatus.inStock);
      expect(
        summary.image.url,
        'assets/images/products/aria-pendant-black.webp',
      );
    });
  });

  group('ProductSummary / ProductPage / MockCatalog', () {
    test('ProductSummary serialises stockStatus as snake_case', () {
      final summary = Product.fromJson(_productJson()).toSummary();
      final json = _roundTrip(summary.toJson());
      expect(json['stockStatus'], 'in_stock');
      expect(json['salePrice'], isNull);
      expect(json.containsKey('salePrice'), isTrue);
      expect(ProductSummary.fromJson(json), summary);
    });

    test('ProductPage round-trips', () {
      final page = ProductPage(
        items: [Product.fromJson(_productJson()).toSummary()],
        total: 16,
        page: 1,
        pageSize: 10,
      );
      expect(ProductPage.fromJson(_roundTrip(page.toJson())), page);
    });

    test('MockCatalog round-trips and rejects unknown root keys', () {
      final json = {
        'catalogVersion': 1,
        'products': [_productJson()],
      };
      final catalog = MockCatalog.fromJson(json);
      expect(catalog.catalogVersion, 1);
      expect(MockCatalog.fromJson(_roundTrip(catalog.toJson())), catalog);
      expect(
        () => MockCatalog.fromJson({...json, 'extra': true}),
        _checkedFailure<UnrecognizedKeysException>(),
      );
    });
  });
}
