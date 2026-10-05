import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/catalog_providers.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';

/// Riverpod overrides for in-memory M1 catalog without network health probes.
// ignore: strict_top_level_inference
localCatalogOverrides({CatalogSeedDocument? seedOverride}) {
  return [
    localCatalogDataSourceProvider.overrideWithValue(
      LocalCatalogDataSource(
        seedOverride: seedOverride ?? buildDefaultCatalogSeed(),
      ),
    ),
    catalogTestHealthProbeOverride,
  ];
}

/// In-memory catalog for widget tests (avoids asset loading and spinner settle loops).
final catalogTestOverrides = localCatalogOverrides();

Future<void> pumpUntilSettled(WidgetTester tester, {int maxPumps = 20}) async {
  for (var i = 0; i < maxPumps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}
