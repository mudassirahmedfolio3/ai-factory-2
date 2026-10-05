import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CatalogApi
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    // Get product detail
    //
    // Product detail including description, images, and variants with per-variant stock.
    //
    //Future<ProductDetail> getProductById(String productId) async
    test('test getProductById', () async {
      // TODO
    });

    // List categories
    //
    //Future<CategoryListResponse> listCategories({ int page, int pageSize }) async
    test('test listCategories', () async {
      // TODO
    });

    // List products
    //
    // Paginated product summaries for the browse screen. Prices in integer cents USD.
    //
    //Future<ProductListResponse> listProducts({ int page, int pageSize, String categoryId }) async
    test('test listProducts', () async {
      // TODO
    });

  });
}
