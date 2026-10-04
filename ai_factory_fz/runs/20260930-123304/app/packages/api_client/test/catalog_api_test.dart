import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CatalogApi
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    // Get product detail
    //
    // Returns full details of one active product. Public, no authentication required.
    //
    //Future<ProductDetail> getProduct(String productId) async
    test('test getProduct', () async {
      // TODO
    });

    // List active products (paginated)
    //
    // Returns active products ordered by sortOrder then name. Public, no authentication required.
    //
    //Future<ProductPage> listProducts({ int page, int pageSize }) async
    test('test listProducts', () async {
      // TODO
    });

  });
}
