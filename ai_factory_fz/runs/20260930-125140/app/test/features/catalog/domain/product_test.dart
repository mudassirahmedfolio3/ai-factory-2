import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/money.dart';
import 'package:shopease_app/features/catalog/domain/product.dart';

void main() {
  final detailJson = <String, dynamic>{
    'id': '7d1f0c1e-2a4b-4c3d-9e8f-0a1b2c3d4e5f',
    'slug': 'classic-cotton-tee',
    'name': 'Classic Cotton Tee',
    'description': 'Soft everyday tee.',
    'imageUrl': null,
    'imageAlt': 'White cotton t-shirt on a plain background',
    'priceFrom': {'amountMinor': 1999, 'currency': 'USD'},
    'inStock': true,
    'sizes': ['S', 'M'],
    'colors': ['White'],
    'variants': [
      {
        'id': '11111111-1111-4111-8111-111111111111',
        'sku': 'TEE-CLS-WHT-S',
        'size': 'S',
        'color': 'White',
        'price': {'amountMinor': 1999, 'currency': 'USD'},
        'stockQuantity': 0,
        'inStock': false,
      },
      {
        'id': '22222222-2222-4222-8222-222222222222',
        'sku': 'TEE-CLS-WHT-M',
        'size': 'M',
        'color': null,
        'price': {'amountMinor': 2199, 'currency': 'USD'},
        'stockQuantity': 4,
        'inStock': true,
      },
    ],
  };

  test('ProductDetail parses the OpenAPI ProductDetail shape', () {
    final detail = ProductDetail.fromJson(detailJson);
    expect(detail.name, 'Classic Cotton Tee');
    expect(detail.imageUrl, isNull);
    expect(detail.priceFrom, const Money(amountMinor: 1999, currency: 'USD'));
    expect(detail.variants, hasLength(2));
    expect(detail.variants.first.inStock, isFalse);
    expect(detail.variants.last.color, isNull);
    expect(detail.variants.last.price.amountMinor, 2199);
  });

  test('ProductDetail JSON round-trips with the same field names', () {
    final detail = ProductDetail.fromJson(detailJson);
    expect(detail.toJson(), detailJson);
  });

  test('toSummary projects to the ProductSummary shape', () {
    final summary = ProductDetail.fromJson(detailJson).toSummary();
    expect(summary.toJson().keys.toSet(), {
      'id',
      'slug',
      'name',
      'imageUrl',
      'imageAlt',
      'priceFrom',
      'inStock',
    });
    expect(summary.inStock, isTrue);
  });
}
