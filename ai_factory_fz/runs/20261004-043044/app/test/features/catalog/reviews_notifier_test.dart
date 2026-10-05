import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/features/catalog/data/catalog_providers.dart';

import '../../helpers/catalog_test_overrides.dart';
import 'package:shopease_app/features/catalog/presentation/reviews_notifier.dart';

void main() {
  const productId = 'p1111111-1111-4111-8111-111111111101';

  test('ReviewsNotifier paginates locally', () async {
    final container = ProviderContainer(
      overrides: localCatalogOverrides(),
    );
    addTearDown(container.dispose);

    final first = await container.read(
      reviewsNotifierProvider(productId).future,
    );
    expect(first.items.length, 2);
    expect(first.hasMore, isFalse);

    await container
        .read(reviewsNotifierProvider(productId).notifier)
        .loadMore();
    final after = container
        .read(reviewsNotifierProvider(productId))
        .requireValue;
    expect(after.items.length, 2);
  });

  test('ReviewsNotifier loadMore with smaller page size', () async {
    final container = ProviderContainer(
      overrides: localCatalogOverrides(),
    );
    addTearDown(container.dispose);

    final repository = container.read(catalogRepositoryProvider);
    final page1 = await repository.listProductReviews(
      productId,
      page: 1,
      pageSize: 1,
    );
    expect(page1.items.length, 1);
    expect(page1.total, 2);

    final page2 = await repository.listProductReviews(
      productId,
      page: 2,
      pageSize: 1,
    );
    expect(page2.items.length, 1);
  });
}
