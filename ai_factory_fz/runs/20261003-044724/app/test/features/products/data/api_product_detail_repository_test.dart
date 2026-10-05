import 'package:api_client/api_client.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/products/data/product_detail_repository.dart';

void main() {
  const productId = '11111111-1111-4111-8111-111111111111';

  test(
    'ApiProductDetailRepository maps getProductById JSON to ProductDetailModel',
    () async {
      final dio = Dio(
        BaseOptions(baseUrl: 'http://test.local/api/v1'),
      );
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            expect(options.path, '/products/$productId');
            handler.resolve(
              Response<Map<String, dynamic>>(
                requestOptions: options,
                statusCode: 200,
                data: {
                  'id': productId,
                  'name': 'Citrus Hand Soap',
                  'brand': 'ShopEase',
                  'description': 'Fresh citrus scent.',
                  'category': {
                    'id': '22222222-2222-4222-8222-222222222222',
                    'name': 'Personal Care',
                    'slug': 'personal-care',
                  },
                  'price': {'amountCents': 799, 'currency': 'USD'},
                  'primaryImageUrl': 'https://example.com/soap.jpg',
                  'availability': 'in_stock',
                  'variants': [
                    {
                      'id': 'var-1',
                      'sku': 'SOAP-STD',
                      'name': 'Standard',
                      'price': {'amountCents': 799, 'currency': 'USD'},
                      'stockAvailable': 12,
                      'isDefault': true,
                    },
                  ],
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
      final repository = ApiProductDetailRepository(client);

      final detail = await repository.fetchProductDetail(productId);

      expect(detail, isNotNull);
      expect(detail!.id, productId);
      expect(detail.name, 'Citrus Hand Soap');
      expect(detail.description, 'Fresh citrus scent.');
      expect(detail.categorySlug, 'personal-care');
      expect(detail.images, hasLength(1));
      expect(detail.images.first.url, 'https://example.com/soap.jpg');
      expect(detail.variants, hasLength(1));
      expect(detail.variants.first.amountCents, 799);
      expect(detail.variants.first.isAvailable, isTrue);
      expect(detail.isAvailable, isTrue);
    },
  );

  test('ApiProductDetailRepository returns no reviews from API slice', () async {
    final dio = Dio(
      BaseOptions(baseUrl: 'http://test.local/api/v1'),
    );
    final client = ApiClient(
      dio: dio,
      basePathOverride: 'http://test.local/api/v1',
    );
    final repository = ApiProductDetailRepository(client);

    final reviews = await repository.fetchReviews(productId);

    expect(reviews, isEmpty);
  });
}
