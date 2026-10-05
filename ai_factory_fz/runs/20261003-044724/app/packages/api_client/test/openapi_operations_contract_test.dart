import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

/// Verifies the generated dart-dio surface covers M3 Release 2 operations.
void main() {
  group('ApiClient operation surface', () {
    late ApiClient client;

    setUp(() {
      client = ApiClient(basePathOverride: 'http://test.local/api/v1');
    });

    test('exposes all M3 API groups including Auth and Orders', () {
      expect(client.getAuthApi(), isA<AuthApi>());
      expect(client.getCartApi(), isA<CartApi>());
      expect(client.getCatalogApi(), isA<CatalogApi>());
      expect(client.getCheckoutApi(), isA<CheckoutApi>());
      expect(client.getHealthApi(), isA<HealthApi>());
      expect(client.getHomeApi(), isA<HomeApi>());
      expect(client.getOrdersApi(), isA<OrdersApi>());
      expect(client.getSupportApi(), isA<SupportApi>());
      expect(client.getUsersApi(), isA<UsersApi>());
      expect(client.getWishlistApi(), isA<WishlistApi>());
    });

    test('uses server URLs that already include the /api/v1 prefix', () {
      expect(ApiClient.basePath, 'http://10.0.2.2:3000/api/v1');
      expect(client.dio.options.baseUrl, 'http://test.local/api/v1');
    });
  });

  group('OpenAPI model deserialization', () {
    test('ProductSummary round-trips required catalog list fields', () {
      final json = {
        'id': '11111111-1111-4111-8111-111111111111',
        'name': 'Demo SKU',
        'brand': 'ShopEase',
        'category': {
          'id': '22222222-2222-4222-8222-222222222222',
          'name': 'Home & Lifestyle',
          'slug': 'home-lifestyle',
        },
        'primaryImageUrl': 'https://example.com/item.jpg',
        'price': {'amountCents': 1999, 'currency': 'USD'},
        'availability': 'in_stock',
      };

      final product = standardSerializers.deserializeWith(
        ProductSummary.serializer,
        json,
      )!;

      expect(product.id, json['id']);
      expect(product.name, json['name']);
      expect(product.price.amountCents, 1999);
      expect(product.price.currency, 'USD');
      expect(product.availability, AvailabilityStatus.inStock);
    });

    test('HealthResponse deserializes the documented liveness payload', () {
      final status = standardSerializers.deserializeWith(
        HealthResponse.serializer,
        {
          'status': 'ok',
          'database': 'up',
          'timestamp': '2026-01-01T00:00:00.000Z',
        },
      )!;

      expect(status.status, HealthResponseStatusEnum.ok);
      expect(status.database, HealthResponseDatabaseEnum.up);
    });

    test('AuthResponse deserializes token payload', () {
      final auth = standardSerializers.deserializeWith(
        AuthResponse.serializer,
        {
          'accessToken': 'access',
          'refreshToken': 'refresh',
          'expiresInSeconds': 900,
          'user': {
            'id': '11111111-1111-4111-8111-111111111111',
            'email': 'shopper@example.com',
          },
        },
      )!;

      expect(auth.accessToken, 'access');
      expect(auth.user.email, 'shopper@example.com');
    });
  });
}
