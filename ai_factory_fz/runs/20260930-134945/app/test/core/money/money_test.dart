import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/money.dart';

void main() {
  group('formatGbp', () {
    test('formats with integer arithmetic', () {
      expect(formatGbp(0), '£0.00');
      expect(formatGbp(5), '£0.05');
      expect(formatGbp(99), '£0.99');
      expect(formatGbp(100), '£1.00');
      expect(formatGbp(2499), '£24.99');
      expect(formatGbp(123456), '£1,234.56');
      expect(formatGbp(100000000), '£1,000,000.00');
    });
  });

  group('Money', () {
    test('adds and multiplies in pence', () {
      const unit = Money(amountMinor: 1999);
      final line = unit * 3;
      expect(line.amountMinor, 5997);
      expect((line + const Money(amountMinor: 3)).amountMinor, 6000);
      expect(line.format(), '£59.97');
    });

    test('value equality and json round trip (freezed)', () {
      const a = Money(amountMinor: 500);
      expect(a, const Money(amountMinor: 500, currency: 'GBP'));
      expect(Money.fromJson(a.toJson()), a);
    });

    test('rejects mixing currencies', () {
      expect(
        () =>
            const Money(amountMinor: 1) +
            const Money(amountMinor: 1, currency: 'EUR'),
        throwsArgumentError,
      );
    });
  });
}
