import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/formatting/gbp_money_formatter.dart';

void main() {
  test('formatPence renders en-GB GBP from integer pence', () {
    expect(GbpMoneyFormatter.formatPence(4999), '£49.99');
    expect(GbpMoneyFormatter.formatPence(1299), '£12.99');
    expect(GbpMoneyFormatter.formatPence(0), '£0.00');
  });

  test('formatPence rejects negative pence', () {
    expect(() => GbpMoneyFormatter.formatPence(-1), throwsArgumentError);
  });
}
