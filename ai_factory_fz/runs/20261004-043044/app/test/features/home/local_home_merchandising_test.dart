import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/data/local_catalog_data_source.dart';

/// US-001: offline/API-fallback home must surface seeded merchandising from catalog.json.
void main() {
  test('getHome includes banners and new arrivals from bundled M3 catalog.json', () async {
    TestWidgetsFlutterBinding.ensureInitialized();
    final local = LocalCatalogDataSource();
    final home = await local.getHome();

    expect(
      home.banners.length,
      greaterThanOrEqualTo(2),
      reason: 'catalog.json seeds two homeBanners for offline demo',
    );
    expect(
      home.newArrivals,
      isNotEmpty,
      reason: 'M3 home merchandising includes new arrivals',
    );
  });
}
