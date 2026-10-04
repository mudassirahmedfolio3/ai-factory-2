import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/money.dart';

void main() {
  group('formatMoney', () {
    test('formats integer cents as USD', () {
      expect(formatMoney(const Money.usd(12999)), r'$129.99');
    });

    test('pads cents and handles zero and sub-dollar amounts', () {
      expect(formatMoney(const Money.usd(0)), r'$0.00');
      expect(formatMoney(const Money.usd(5)), r'$0.05');
      expect(formatMoney(const Money.usd(999)), r'$9.99');
      expect(formatMoney(const Money.usd(15000)), r'$150.00');
    });

    test('groups thousands with commas', () {
      expect(formatMoney(const Money.usd(100000)), r'$1,000.00');
      expect(formatMoney(const Money.usd(123456789)), r'$1,234,567.89');
      expect(formatMoney(const Money.usd(99999)), r'$999.99');
    });

    test('negative minor units are prefixed with a minus sign', () {
      expect(formatMinorUnits(-1250), r'-$12.50');
    });
  });

  group('Money', () {
    test('adds and multiplies with integer arithmetic', () {
      expect(const Money.usd(1999) + const Money.usd(1), const Money.usd(2000));
      expect(const Money.usd(1999) * 3, const Money.usd(5997));
    });

    test('rejects mixed currencies', () {
      expect(
        () => const Money.usd(1) + const Money(1, currency: 'EUR'),
        throwsArgumentError,
      );
    });

    test('round-trips the OpenAPI Money JSON shape', () {
      final money = Money.fromJson({'amountMinor': 12999, 'currency': 'USD'});
      expect(money, const Money.usd(12999));
      expect(money.toJson(), {'amountMinor': 12999, 'currency': 'USD'});
    });

    test('rejects non-integer or negative amounts', () {
      expect(
        () => Money.fromJson({'amountMinor': 129.99, 'currency': 'USD'}),
        throwsFormatException,
      );
      expect(
        () => Money.fromJson({'amountMinor': -1, 'currency': 'USD'}),
        throwsFormatException,
      );
    });
  });
}
