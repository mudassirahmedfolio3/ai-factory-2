import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_repository.dart';

void main() {
  const repo = LocalCatalogRepository();

  test('bundles exactly the 8 required beauty products', () {
    final products = repo.listProducts();
    expect(products, hasLength(8));
    expect(products.map((p) => p.id).toList(), [
      'lipstick',
      'foundation',
      'mascara',
      'face-serum',
      'moisturizer',
      'perfume',
      'nail-polish',
      'brush-set',
    ]);
  });

  test('ids are unique, prices are positive USD cents', () {
    final products = repo.listProducts();
    expect(products.map((p) => p.id).toSet(), hasLength(products.length));
    for (final p in products) {
      expect(p.priceCents, greaterThan(0));
      expect(p.currency, 'USD');
      expect(p.name, isNotEmpty);
      expect(p.description, isNotEmpty);
    }
  });

  test('findById returns the product or null for unknown ids', () {
    expect(repo.findById('lipstick')?.priceCents, 1999);
    expect(repo.findById('does-not-exist'), isNull);
  });
}
