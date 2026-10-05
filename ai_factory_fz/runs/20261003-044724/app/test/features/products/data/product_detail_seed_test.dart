import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  late Map<String, dynamic> detailSeed;

  setUpAll(() {
    final file = File('assets/seed/product_detail_seed.json');
    detailSeed = jsonDecode(file.readAsStringSync()) as Map<String, dynamic>;
  });

  test('seeded product with reviews exposes rating and review entries', () {
    final products = (detailSeed['products'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
    final reviews = detailSeed['reviews'] as Map<String, dynamic>;

    final soap = products.firstWhere((p) => p['id'] == 'seed-product-1');
    expect(soap['averageRating'], 4.5);
    expect(soap['reviewCount'], 2);
    expect(soap['isAvailable'], isTrue);

    final soapReviews = (reviews['seed-product-1'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
    expect(soapReviews, hasLength(2));
    expect(soapReviews.first['authorName'], 'Maya');
    expect(
      soapReviews.first['comment'],
      'Fresh scent and non-drying formula. Great for daily use.',
    );
  });

  test('seeded unavailable product blocks purchase via availability flags', () {
    final products = (detailSeed['products'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
    final diffuser = products.firstWhere((p) => p['id'] == 'seed-product-10');
    expect(diffuser['isAvailable'], isFalse);
    final variants = (diffuser['variants'] as List<dynamic>)
        .cast<Map<String, dynamic>>();
    expect(variants.every((v) => v['isAvailable'] == false), isTrue);
  });
}
