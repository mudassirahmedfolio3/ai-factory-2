import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for CatalogApi
void main() {
  final instance = ApiClient().getCatalogApi();

  group(CatalogApi, () {
    // Get product detail
    //
    //Future<ProductDetail> getProductById(String productId) async
    test('test getProductById', () async {
      // TODO
    });

    // List product categories
    //
    //Future<CategoryListResponse> listCategories() async
    test('test listCategories', () async {
      // TODO
    });

    // List and search products
    //
    //Future<ProductListResponse> listProducts({ int page, int pageSize, String q, String category, String brand, int minPriceCents, int maxPriceCents, AvailabilityFilter availability, String sort }) async
    test('test listProducts', () async {
      // TODO
    });

  });
}
