import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';

void main() {
  late Map<String, dynamic> catalog;
  late List<Map<String, dynamic>> products;

  setUpAll(() {
    final file = File('assets/seed/catalog_seed.json');
    catalog = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
    products = (catalog['products'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
  });

  test('seeds 12–20 catalog products with name, image, and integer prices', () {
    expect(products.length, inInclusiveRange(12, 20));
    for (final product in products) {
      expect(product['id'], isA<String>());
      expect(product['name'], isA<String>());
      expect(product['imageUrl'], isA<String>());
      expect(product['priceMinor'], isA<int>());
      expect(product['currency'], 'USD');
      expect(product['categorySlug'], isA<String>());
      expect(product['isAvailable'], isA<bool>());
    }
  });

  test('seed covers launch categories and value/mid/premium price bands', () {
    final categories = products.map((p) => p['categorySlug']).toSet();
    expect(
      categories,
      containsAll(<String>[
        'everyday-essentials',
        'home-lifestyle',
        'personal-care',
        'gift-friendly',
      ]),
    );

    final valueCount = products
        .where((p) => matchesPriceBand(p['priceMinor'] as int, ProductPriceBand.value))
        .length;
    final midCount = products
        .where(
          (p) => matchesPriceBand(p['priceMinor'] as int, ProductPriceBand.midRange),
        )
        .length;
    final premiumCount = products
        .where(
          (p) => matchesPriceBand(p['priceMinor'] as int, ProductPriceBand.premium),
        )
        .length;

    expect(valueCount, greaterThan(0));
    expect(midCount, greaterThan(0));
    expect(premiumCount, greaterThan(0));
    expect(
      products.every((p) {
        final cents = p['priceMinor'] as int;
        return cents >= 500 && cents <= 15000;
      }),
      isTrue,
    );
  });

  test('seed includes at least one unavailable product for availability QA', () {
    expect(products.any((p) => p['isAvailable'] == false), isTrue);
    expect(products.any((p) => p['isAvailable'] == true), isTrue);
  });
}
