import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/catalog_query_engine.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';
import 'package:shopease_app/features/catalog/domain/models/catalog_money.dart';
import 'package:shopease_app/features/catalog/domain/models/lighting_specification.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';
import 'package:shopease_app/features/catalog/domain/models/product_variant.dart';

CatalogProduct _minimalProduct({
  required String id,
  required int popularityRank,
  required int unitsSold90Days,
}) {
  return CatalogProduct(
    id: id,
    name: 'Test $id',
    brand: 'Luminex',
    brandSlug: 'luminex',
    slug: 'test-$id',
    description: 'Test product',
    categoryId: 'c1111111-1111-4111-8111-111111111101',
    primaryImageUrl: 'assets/images/products/placeholder.png',
    variants: [
      ProductVariant(
        id: 'v-$id',
        sku: 'SKU-$id',
        label: 'Default',
        price: CatalogMoney.gbp(1000),
        stockQuantity: 1,
        availableQuantity: 1,
        isDefault: true,
      ),
    ],
    images: const [],
    specs: const LightingSpecification(),
    reviews: const [],
    popularityRank: popularityRank,
    unitsSold90Days: unitsSold90Days,
    createdAt: DateTime.utc(2025, 1, 1),
  );
}

void main() {
  test('popularity sort tie-breaks equal rank by units sold in last 90 days', () {
    final engine = CatalogQueryEngine(categories: const [], products: const []);
    final list = [
      _minimalProduct(id: 'a', popularityRank: 5, unitsSold90Days: 10),
      _minimalProduct(id: 'b', popularityRank: 5, unitsSold90Days: 50),
    ];
    engine.sortProducts(list, ProductSort.popularity);
    expect(list.first.id, 'b');
    expect(list.last.id, 'a');
  });

  test('popularity sort orders unset rank after ranked products', () {
    final seed = buildDefaultCatalogSeed();
    final engine = CatalogQueryEngine(
      categories: seed.categories,
      products: seed.products,
    );
    final list = List<CatalogProduct>.from(seed.products);
    engine.sortProducts(list, ProductSort.popularity);

    final nullRankIndex = list.indexWhere((p) => p.popularityRank == null);
    final lastRankedIndex = list.lastIndexWhere((p) => p.popularityRank != null);
    expect(nullRankIndex, greaterThan(lastRankedIndex));
  });
}
