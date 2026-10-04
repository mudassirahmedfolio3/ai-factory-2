import 'package:api_client/api_client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/checkout/data/checkout_repository.dart';

void main() {
  test('CheckoutRepository maps quote JSON to CheckoutQuoteView', () async {
    final dio = Dio(BaseOptions(baseUrl: 'http://test.local/api/v1'));
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          expect(options.path, '/checkout/quote');
          handler.resolve(
            Response<Map<String, dynamic>>(
              requestOptions: options,
              statusCode: 200,
              data: {
                'lines': [
                  {
                    'id': '11111111-1111-4111-8111-111111111111',
                    'variantId': '22222222-2222-4222-8222-222222222222',
                    'productId': '33333333-3333-4333-8333-333333333333',
                    'productName': 'Citrus Hand Soap',
                    'variantName': '300 ml',
                    'quantity': 2,
                    'unitPrice': {'amountCents': 799, 'currency': 'USD'},
                    'lineTotal': {'amountCents': 1598, 'currency': 'USD'},
                  },
                ],
                'subtotal': {'amountCents': 1598, 'currency': 'USD'},
                'discount': {'amountCents': 0, 'currency': 'USD'},
                'shipping': {'amountCents': 599, 'currency': 'USD'},
                'tax': {'amountCents': 128, 'currency': 'USD'},
                'total': {'amountCents': 2325, 'currency': 'USD'},
                'coupon': {'valid': true, 'code': 'SAVE10'},
                'taxDisclaimer': 'Final tax may vary.',
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
    final repository = CheckoutRepository(client);
    final quote = await repository.fetchQuote(
      shippingAddress: ShippingAddress(
        (b) => b
          ..fullName = 'Ada Lovelace'
          ..line1 = '123 Main St'
          ..city = 'Austin'
          ..region = 'TX'
          ..postalCode = '78701'
          ..country = ShippingAddressCountryEnum.US,
      ),
      useServerCart: false,
      guestLines: BuiltList<CartLineInput>([
        CartLineInput(
          (b) => b
            ..variantId = '22222222-2222-4222-8222-222222222222'
            ..quantity = 2,
        ),
      ]),
    );

    expect(quote.lines, hasLength(1));
    expect(quote.subtotalCents, 1598);
    expect(quote.shippingCents, 599);
    expect(quote.totalCents, 2325);
    expect(quote.taxDisclaimer, 'Final tax may vary.');
  });
}
