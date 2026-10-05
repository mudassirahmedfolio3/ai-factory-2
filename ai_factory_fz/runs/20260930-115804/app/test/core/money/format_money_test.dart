import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/money/format_money.dart';

void main() {
  group('formatMoney', () {
    test('formats USD cents with integer arithmetic', () {
      expect(formatMoney(1999, 'USD'), r'$19.99');
      expect(formatMoney(999, 'USD'), r'$9.99');
      expect(formatMoney(6500, 'USD'), r'$65.00');
      expect(formatMoney(5, 'USD'), r'$0.05');
      expect(formatMoney(0, 'USD'), r'$0.00');
    });

    test('is case-insensitive for currency code', () {
      expect(formatMoney(1575, 'usd'), r'$15.75');
    });

    test('prefixes unknown currencies with their code', () {
      expect(formatMoney(1999, 'EUR'), 'EUR 19.99');
    });

    test('rejects negative amounts', () {
      expect(() => formatMoney(-1, 'USD'), throwsArgumentError);
    });
  });
}
