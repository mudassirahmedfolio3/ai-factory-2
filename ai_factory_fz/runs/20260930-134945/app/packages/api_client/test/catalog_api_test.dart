import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CatalogApi
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    // Get one active product with lighting specifications
    //
    //Future<ProductDetail> getProduct(String productId) async
    test('test getProduct', () async {
      // TODO
    });

    // List active products
    //
    // Returns active products ordered by name ascending, then id ascending.
    //
    //Future<ProductPage> listProducts({ int page, int pageSize }) async
    test('test listProducts', () async {
      // TODO
    });

  });
}
