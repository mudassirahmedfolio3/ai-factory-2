import 'package:api_client/api_client.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/catalog_repository.dart';
import 'package:shopease_app/features/products/domain/catalog_models.dart';

void main() {
  test('ApiCatalogRepository maps listProducts JSON to CatalogProduct models', () async {
    const productId = '11111111-1111-4111-8111-111111111111';
    final dio = Dio(
      BaseOptions(baseUrl: 'http://test.local/api/v1'),
    );
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          expect(options.path, '/products');
          expect(options.queryParameters['pageSize'], 100);
          handler.resolve(
            Response<Map<String, dynamic>>(
              requestOptions: options,
              statusCode: 200,
              data: {
                'items': [
                  {
                    'id': productId,
                    'name': 'Citrus Hand Soap',
                    'brand': 'ShopEase',
                    'category': {
                      'id': '22222222-2222-4222-8222-222222222222',
                      'name': 'Personal Care',
                      'slug': 'personal-care',
                    },
                    'primaryImageUrl': 'https://example.com/soap.jpg',
                    'price': {'amountCents': 799, 'currency': 'USD'},
                    'availability': 'in_stock',
                  },
                ],
                'total': 1,
                'page': 1,
                'pageSize': 100,
              },
            ),
          );
        },
      ),
    );

    final client = ApiClient(
      dio: dio,
      basePathOverride: 'http://test.local/api/v1',
    );
    final repository = ApiCatalogRepository(client);

    final result = await repository.listProducts(const ProductListQuery());
    final products = result.items;

    expect(products, hasLength(1));
    expect(products.first.id, productId);
    expect(products.first.name, 'Citrus Hand Soap');
    expect(products.first.categorySlug, 'personal-care');
    expect(products.first.categoryName, 'Personal Care');
    expect(products.first.imageUrl, 'https://example.com/soap.jpg');
    expect(products.first.amountCents, 799);
    expect(products.first.currencyCode, 'USD');
    expect(products.first.isAvailable, isTrue);
  });
}
