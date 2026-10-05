import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/money.dart';
import 'package:shopease_app/core/money/money_formatter.dart';

void main() {
  const formatter = MoneyFormatter();

  group('MoneyFormatter (USD, en_US)', () {
    test('formats 1999 cents as \$19.99', () {
      expect(
        formatter.format(const Money(amountMinor: 1999, currency: 'USD')),
        r'$19.99',
      );
    });

    test('formats 0 cents as \$0.00', () {
      expect(
        formatter.format(const Money(amountMinor: 0, currency: 'USD')),
        r'$0.00',
      );
    });

    test('formats 100000 cents with grouping as \$1,000.00', () {
      expect(
        formatter.format(const Money(amountMinor: 100000, currency: 'USD')),
        r'$1,000.00',
      );
    });

    test('keeps single-cent precision', () {
      expect(
        formatter.format(const Money(amountMinor: 5, currency: 'USD')),
        r'$0.05',
      );
    });
  });

  test('symbol and digits are derived from the currency code', () {
    // EUR uses 2 digits and a different symbol; JPY has 0 decimal digits.
    expect(
      formatter.format(const Money(amountMinor: 1999, currency: 'EUR')),
      '€19.99',
    );
    expect(
      formatter.format(const Money(amountMinor: 1999, currency: 'JPY')),
      '¥1,999',
    );
  });

  group('Money arithmetic is integer-only', () {
    test('times multiplies minor units', () {
      expect(
        const Money(amountMinor: 1999, currency: 'USD').times(3),
        const Money(amountMinor: 5997, currency: 'USD'),
      );
    });

    test('plus adds same-currency amounts and rejects mixed currencies', () {
      const a = Money(amountMinor: 1999, currency: 'USD');
      expect(
        a.plus(const Money(amountMinor: 1, currency: 'USD')),
        const Money(amountMinor: 2000, currency: 'USD'),
      );
      expect(
        () => a.plus(const Money(amountMinor: 1, currency: 'EUR')),
        throwsArgumentError,
      );
    });

    test('JSON round-trip matches the OpenAPI Money schema', () {
      const m = Money(amountMinor: 1999, currency: 'USD');
      expect(m.toJson(), {'amountMinor': 1999, 'currency': 'USD'});
      expect(Money.fromJson({'amountMinor': 1999, 'currency': 'USD'}), m);
    });
  });
}
