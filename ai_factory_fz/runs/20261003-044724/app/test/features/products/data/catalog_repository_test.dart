// QA regression test for Milestone M2 / US-006 AC2:
//
// "Given Dart API client generation or integration does not pass
// analyze/tests in time for the demo when the Flutter app is launched for
// the client meeting then the M1 local mock catalog path still works ...
// without blocking the showable app."
//
// catalogRepositoryProvider must default to MockCatalogRepository (reading
// assets/seed/catalog_seed.json) unless USE_API_CATALOG=true is explicitly
// passed at build time. This pins that default down so a future change
// cannot silently switch the demo over to the (currently unverified/blocked)
// API-backed path.
import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/catalog_source_config.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';

/// Loads the real on-disk seed asset without requiring the full Flutter
/// asset-bundling pipeline, keeping this test hermetic like the sibling
/// catalog_seed_test.dart (which reads the same file via dart:io).
class _FileAssetBundle extends AssetBundle {
  @override
  Future<ByteData> load(String key) async {
    final bytes = await File(key).readAsBytes();
    return ByteData.view(bytes.buffer);
  }
}

void main() {
  test('useApiCatalog defaults to false for demo-safe M1 catalog path', () {
    expect(useApiCatalog, isFalse);
  });

  test(
    'catalogRepositoryProvider defaults to MockCatalogRepository (local seed, no backend dependency)',
    () {
      final container = ProviderContainer();
      addTearDown(container.dispose);

      final repository = container.read(catalogRepositoryProvider);

      expect(repository, isA<MockCatalogRepository>());
      expect(repository, isNot(isA<ApiCatalogRepository>()));
    },
  );

  test(
    'MockCatalogRepository loads products from the bundled seed asset without network access',
    () async {
      final repository = MockCatalogRepository(assetBundle: _FileAssetBundle());

      final products = await repository.fetchProducts();

      expect(products, isNotEmpty);
      expect(products.length, inInclusiveRange(12, 20));
    },
  );
}
