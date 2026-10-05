import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

/// tests for CatalogApi product endpoints
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    test('test listProducts', () async {
      expect(instance, isA<CatalogApi>());
    });

    test('test getProductById', () async {
      expect(instance, isA<CatalogApi>());
    });
  });
}
