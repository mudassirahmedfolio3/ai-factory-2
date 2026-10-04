import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/catalog_source_config.dart';
import 'package:shopease_app/features/products/data/product_detail_repository.dart';

void main() {
  test('useApiCatalog defaults to false for demo-safe mock detail path', () {
    expect(useApiCatalog, isFalse);
  });

  test(
    'productDetailRepositoryProvider defaults to MockProductDetailRepository',
    () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final repository = container.read(productDetailRepositoryProvider);

      expect(repository, isA<MockProductDetailRepository>());
      expect(repository, isNot(isA<ApiProductDetailRepository>()));
    },
  );
}
