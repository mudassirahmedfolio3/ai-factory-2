import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CatalogApi
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    // Get product detail
    //
    // Product detail including all active variants with per-variant price and stock. Public; no authentication.
    //
    //Future<ProductDetail> getProduct(String productId) async
    test('test getProduct', () async {
      // TODO
    });

    // List active products
    //
    // Paginated list of active products ordered by name ascending. Public; no authentication.
    //
    //Future<ProductPage> listProducts({ int page, int pageSize }) async
    test('test listProducts', () async {
      // TODO
    });

  });
}
