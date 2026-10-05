import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/catalog_repository_impl.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';
import 'package:shopease_app/features/catalog/domain/catalog_list_query.dart';
import 'package:shopease_app/features/catalog/domain/catalog_repository.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';

void main() {
  late CatalogRepository repository;

  setUp(() {
    repository = CatalogRepositoryImpl(
      local: LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
    );
  });

  test('seed contains 16 products across taxonomy categories', () async {
    final home = await repository.getHome();
    expect(home.categories.length, 7);
    expect(home.featuredProducts, isNotEmpty);

    final all = await repository.listProducts(const CatalogListQuery());
    expect(all.total, 16);
  });

  test('search by product name and SKU', () async {
    final byName = await repository.listProducts(
      const CatalogListQuery(q: 'Modern LED Ceiling Light'),
    );
    expect(byName.total, 1);
    expect(byName.items.single.name, 'Modern LED Ceiling Light');

    final bySku = await repository.listProducts(
      const CatalogListQuery(q: 'CL-1001'),
    );
    expect(bySku.total, 1);

    final byBrand = await repository.listProducts(
      const CatalogListQuery(q: 'Luminex'),
    );
    expect(byBrand.total, greaterThan(1));
  });

  test('empty search returns no items', () async {
    final none = await repository.listProducts(
      const CatalogListQuery(q: 'no-such-product-xyz'),
    );
    expect(none.total, 0);
    expect(none.items, isEmpty);
  });

  test('category slug filter includes child categories', () async {
    final ceiling = await repository.listProducts(
      const CatalogListQuery(categorySlug: 'ceiling-lights'),
    );
    expect(ceiling.total, 3);

    final pendantOnly = await repository.listProducts(
      const CatalogListQuery(categorySlug: 'pendant-lights'),
    );
    expect(pendantOnly.total, 1);
  });

  test('price filter uses listing pence without floats', () async {
    final mid = await repository.listProducts(
      const CatalogListQuery(minPriceCents: 4000, maxPriceCents: 5000),
    );
    expect(mid.items.every((p) => p.price.priceMinorUnits >= 4000), isTrue);
    expect(mid.items.every((p) => p.price.priceMinorUnits <= 5000), isTrue);
  });

  test('popularity sort uses rank then 90-day units sold', () async {
    final sorted = await repository.listProducts(
      const CatalogListQuery(sort: ProductSort.popularity),
    );
    final ranks = sorted.items.map((p) => p.popularityRank).toList();
    expect(ranks.first, 1);
    expect(sorted.items.first.name, 'Modern LED Ceiling Light');
  });

  test('price ascending sort orders by listing pence', () async {
    final sorted = await repository.listProducts(
      const CatalogListQuery(sort: ProductSort.priceAsc),
    );
    final prices = sorted.items
        .map((p) => p.price.priceMinorUnits)
        .toList(growable: false);
    for (var i = 1; i < prices.length; i++) {
      expect(prices[i], greaterThanOrEqualTo(prices[i - 1]));
    }
  });

  test('brand filter returns only selected brands', () async {
    final filtered = await repository.listProducts(
      const CatalogListQuery(brands: ['Voltara']),
    );
    expect(filtered.total, greaterThan(0));
    expect(filtered.items.every((p) => p.brand == 'Voltara'), isTrue);
  });

  test('inStockOnly filter excludes fully out-of-stock products', () async {
    final all = await repository.listProducts(const CatalogListQuery());
    expect(all.items.any((p) => !p.inStock), isTrue);
    final inStockOnly = await repository.listProducts(
      const CatalogListQuery(inStockOnly: true),
    );
    expect(inStockOnly.total, lessThan(all.total));
    expect(inStockOnly.items.every((p) => p.inStock), isTrue);
  });

  test('fully out-of-stock product appears in listing with inStock false', () async {
    final listing = await repository.listProducts(
      const CatalogListQuery(q: 'Garden Bollard Light'),
    );
    expect(listing.total, 1);
    expect(listing.items.single.inStock, isFalse);
  });

  test('finish and wattage filters narrow results', () async {
    final byFinish = await repository.listProducts(
      const CatalogListQuery(finish: 'Matte White'),
    );
    expect(byFinish.total, greaterThan(0));

    final byWattage = await repository.listProducts(
      const CatalogListQuery(minWattage: 20, maxWattage: 30),
    );
    expect(byWattage.total, greaterThan(0));
    expect(byWattage.items.every((p) => p.price.priceMinorUnits > 0), isTrue);
  });

  test('listing exposes sale compare-at price in integer pence', () async {
    final listing = await repository.listProducts(
      const CatalogListQuery(q: 'Modern LED Ceiling Light'),
    );
    final item = listing.items.single;
    expect(item.price.priceMinorUnits, 4999);
    expect(item.compareAtPrice?.priceMinorUnits, 5999);
  });

  test('product detail and paginated reviews', () async {
    const productId = 'p1111111-1111-4111-8111-111111111101';
    final detail = await repository.getProductById(productId);
    expect(detail.variants.length, 2);
    expect(detail.specs.wattageW, 24);
    expect(detail.rating.reviewCount, 2);

    final reviews = await repository.listProductReviews(
      productId,
      page: 1,
      pageSize: 1,
    );
    expect(reviews.total, 2);
    expect(reviews.items.length, 1);
    expect(reviews.rating.reviewCount, 2);
  });

  test('loads catalog.json asset bundle shape', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final fromAsset = LocalCatalogDataSource();
    final doc = await fromAsset.loadDocument();
    expect(doc.products.length, 24);
  });

  test('getCategoryBySlug throws when missing', () async {
    expect(
      () => repository.getCategoryBySlug('missing-slug'),
      throwsA(isA<CatalogNotFoundException>()),
    );
  });
}
