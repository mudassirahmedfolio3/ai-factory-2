import 'package:test/test.dart';
import 'package:api_client/api_client.dart';

// tests for Money
void main() {
  final instance = MoneyBuilder();
  // TODO add properties to the builder and call build()

  group(Money, () {
    // Amount in minor units, e.g. 1299 means 12.99 GBP
    // int amountMinor
    test('to test the property `amountMinor`', () async {
      // TODO
    });

    // ISO 4217 currency code. Only GBP is supported in this release.
    // String currency
    test('to test the property `currency`', () async {
      // TODO
    });

  });
}
