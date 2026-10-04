import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

void main() {
  test('ProductVariant exposes M3 stock fields', () {
    final instance = ProductVariant(
      (b) => b
        ..id = '11111111-1111-4111-8111-111111111111'
        ..sku = 'SKU-1'
        ..name = 'Standard'
        ..price.replace(
          Money(
            (m) => m
              ..amountCents = 999
              ..currency = 'USD',
          ),
        )
        ..stockAvailable = 5
        ..isDefault = true,
    );

    expect(instance.stockAvailable, 5);
    expect(instance.isDefault, isTrue);
  });
}
