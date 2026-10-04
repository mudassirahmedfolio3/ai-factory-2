import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/utils/money_formatter.dart';

void main() {
  test('formats integer minor units with ISO 4217 currency symbol', () {
    expect(
      MoneyFormatter.formatMinorUnits(
        amountMinorUnits: 799,
        currencyCode: 'USD',
      ),
      '\$7.99',
    );
    expect(
      MoneyFormatter.formatMinorUnits(
        amountMinorUnits: 14999,
        currencyCode: 'USD',
      ),
      '\$149.99',
    );
    expect(
      MoneyFormatter.formatMinorUnits(
        amountMinorUnits: 2500,
        currencyCode: 'USD',
      ),
      '\$25.00',
    );
  });
}
