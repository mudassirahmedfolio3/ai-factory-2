import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/config/pricing_config.dart';

void main() {
  test('pricing constants match the architecture (integer cents)', () {
    expect(kSalesTaxRateBasisPoints, 825);
    expect(kFlatShippingMinor, 999);
    expect(kFreeShippingThresholdMinor, 15000);
    expect(kLowStockThreshold, 5);
    expect(kCatalogPageSize, 10);
    expect(kDefaultCurrency, 'USD');
  });
}
