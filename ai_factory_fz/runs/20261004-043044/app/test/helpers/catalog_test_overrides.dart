import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/catalog_providers.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';
import 'package:shopease_app/features/catalog/data/seed/default_catalog_seed.dart';

/// In-memory catalog for widget tests (avoids asset loading and spinner settle loops).
final catalogTestOverrides = [
  localCatalogDataSourceProvider.overrideWithValue(
    LocalCatalogDataSource(seedOverride: buildDefaultCatalogSeed()),
  ),
];

Future<void> pumpUntilSettled(WidgetTester tester, {int maxPumps = 20}) async {
  for (var i = 0; i < maxPumps; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}
