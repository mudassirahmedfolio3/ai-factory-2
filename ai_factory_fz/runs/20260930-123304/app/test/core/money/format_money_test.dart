import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/format_money.dart';
import 'package:shopease_app/core/money/money.dart';

void main() {
  group('formatMoney', () {
    final cases = <int, String>{
      0: '£0.00',
      5: '£0.05',
      99: '£0.99',
      100: '£1.00',
      1299: '£12.99',
      123450: '£1,234.50',
      100000000: '£1,000,000.00',
    };
    cases.forEach((pence, expected) {
      test('$pence pence -> $expected', () {
        expect(formatMoney(Money.gbp(pence)), expected);
      });
    });

    test('rejects non-GBP currencies', () {
      expect(
        () => formatMoney(const Money(amountMinor: 100, currency: 'EUR')),
        throwsArgumentError,
      );
    });
  });

  group('Money', () {
    test('adds and multiplies in integer pence', () {
      final total = Money.gbp(1299).times(3) + Money.gbp(1);
      expect(total, Money.gbp(3898));
      expect(total.amountMinor, isA<int>());
    });

    test('refuses to mix currencies', () {
      expect(
        () => Money.gbp(1) + const Money(amountMinor: 1, currency: 'EUR'),
        throwsArgumentError,
      );
    });

    test('round-trips the OpenAPI JSON shape', () {
      final money = Money.fromJson({'amountMinor': 1299, 'currency': 'GBP'});
      expect(money, Money.gbp(1299));
      expect(money.toJson(), {'amountMinor': 1299, 'currency': 'GBP'});
    });
  });
}
