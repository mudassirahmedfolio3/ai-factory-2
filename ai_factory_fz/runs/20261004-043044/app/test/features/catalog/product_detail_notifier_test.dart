import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/features/catalog/data/catalog_providers.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_notifier.dart';

void main() {
  const productId = 'p1111111-1111-4111-8111-111111111101';

  ProviderContainer buildContainer() {
    return ProviderContainer(
      overrides: [
        localCatalogDataSourceProvider.overrideWithValue(
          LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
        ),
      ],
    );
  }

  test('ProductDetailNotifier loads product and default variant', () async {
    final container = buildContainer();
    addTearDown(container.dispose);

    final data = await container.read(
      productDetailNotifierProvider(productId).future,
    );

    expect(data.product.name, 'Modern LED Ceiling Light');
    expect(data.selectedVariantId, 'v1111111-1111-4111-8111-111111111101');
    expect(data.selectedVariant?.sku, 'CL-1001-WH');
    expect(data.canAddToCart, isTrue);
    expect(data.previewReviews.length, 2);
  });

  test('ProductDetailNotifier variant selection updates stock state', () async {
    final container = buildContainer();
    addTearDown(container.dispose);

    await container.read(productDetailNotifierProvider(productId).future);
    container
        .read(productDetailNotifierProvider(productId).notifier)
        .selectVariant('v1111111-1111-4111-8111-111111111102');

    final data = container
        .read(productDetailNotifierProvider(productId))
        .requireValue;
    expect(data.selectedVariant?.sku, 'CL-1001-BK');
    expect(data.canAddToCart, isFalse);
  });
}
