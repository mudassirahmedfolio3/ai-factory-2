import 'package:test/test.dart';
import 'package:api_client/api_client.dart';

// tests for Money
void main() {
  final instance = MoneyBuilder();
  // TODO add properties to the builder and call build()

  group(Money, () {
    // Integer minor units (e.g. cents). Never a float.
    // int amountCents
    test('to test the property `amountCents`', () async {
      // TODO
    });

    // ISO 4217 currency code
    // String currency
    test('to test the property `currency`', () async {
      // TODO
    });

  });
}
