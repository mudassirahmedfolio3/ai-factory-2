import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../helpers/catalog_test_overrides.dart';
import 'package:shopease_app/features/catalog/domain/catalog_list_query.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_notifier.dart';

void main() {
  test('ProductListNotifier search and clear search', () async {
    final container = ProviderContainer(
      overrides: localCatalogOverrides(),
    );
    addTearDown(container.dispose);

    final notifier = container.read(productListNotifierProvider.notifier);
    await container.read(productListNotifierProvider.future);

    await notifier.setSearch('Modern LED Ceiling Light');
    var data = container.read(productListNotifierProvider).requireValue;
    expect(data.items.length, 1);

    await notifier.setSearch('no-such-product-xyz');
    data = container.read(productListNotifierProvider).requireValue;
    expect(data.items, isEmpty);
    expect(data.isEmptyDueToSearch, isTrue);

    await notifier.clearSearch();
    data = container.read(productListNotifierProvider).requireValue;
    expect(data.items.length, 16);
  });

  test('ProductListNotifier category route context filters listing', () async {
    final container = ProviderContainer(
      overrides: localCatalogOverrides(),
    );
    addTearDown(container.dispose);

    final notifier = container.read(productListNotifierProvider.notifier);
    await container.read(productListNotifierProvider.future);

    await notifier.applyRouteContext(categorySlug: 'ceiling-lights');
    final data = container.read(productListNotifierProvider).requireValue;
    expect(data.items.length, 3);
    expect(data.query.categorySlug, 'ceiling-lights');
  });

  test(
    'ProductListNotifier reset filters keeps search and category route',
    () async {
      final container = ProviderContainer(
        overrides: localCatalogOverrides(),
      );
      addTearDown(container.dispose);

      final notifier = container.read(productListNotifierProvider.notifier);
      await container.read(productListNotifierProvider.future);

      await notifier.applyQuery(
        const CatalogListQuery(
          q: 'Luminex',
          categorySlug: 'ceiling-lights',
          brands: ['Luminex'],
          inStockOnly: true,
          sort: ProductSort.priceAsc,
        ),
      );
      await notifier.resetFilters();
      final data = container.read(productListNotifierProvider).requireValue;
      expect(data.query.q, 'Luminex');
      expect(data.query.categorySlug, 'ceiling-lights');
      expect(data.query.brands, isEmpty);
      expect(data.query.inStockOnly, isFalse);
      expect(data.query.sort, ProductSort.popularity);
    },
  );

  test('ProductListNotifier reset filters restores popularity listing order', () async {
    final container = ProviderContainer(
      overrides: localCatalogOverrides(),
    );
    addTearDown(container.dispose);

    final notifier = container.read(productListNotifierProvider.notifier);
    await container.read(productListNotifierProvider.future);

    await notifier.setSort(ProductSort.priceAsc);
    var data = container.read(productListNotifierProvider).requireValue;
    expect(data.items.first.name, isNot('Modern LED Ceiling Light'));

    await notifier.resetFilters();
    data = container.read(productListNotifierProvider).requireValue;
    expect(data.query.sort, ProductSort.popularity);
    expect(data.items.first.name, 'Modern LED Ceiling Light');
  });
}
