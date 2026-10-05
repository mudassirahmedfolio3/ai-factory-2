import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

/// tests for CatalogApi listCategories
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    test('test listCategories', () async {
      expect(instance, isA<CatalogApi>());
    });
  });
}
