import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/catalog/domain/product.dart';

Map<String, dynamic> _detailJson({
  int priceMinor = 8999,
  int? salePriceMinor = 6999,
}) => {
  'id': '0b6f1c1e-3a52-4c8e-9a4f-1d2e3f4a5b01',
  'sku': 'LUX-PEN-001',
  'name': 'Aurora Brass Dome Pendant',
  'brand': 'Luxora',
  'category': {
    'id': 'c1a2b3c4-0000-4000-8000-000000000002',
    'slug': 'pendant-lights',
    'name': 'Pendant lights',
  },
  'priceMinor': priceMinor,
  'salePriceMinor': salePriceMinor,
  'currency': 'GBP',
  'stockQuantity': 4,
  'stockStatus': 'low_stock',
  'imageUrl': 'asset://images/products/pendant-01.webp',
  'imageAlt': 'Brass dome pendant',
  'description': 'A pendant.',
  'specifications': {
    'wattageW': 9,
    'dimmable': true,
    'dimensionsMm': {'heightMm': 220, 'diameterMm': 300},
    'ipRating': 'IP44',
  },
};

void main() {
  group('StockStatus.fromQuantity', () {
    test('uses the global low-stock threshold of 5', () {
      expect(StockStatus.fromQuantity(0), StockStatus.outOfStock);
      expect(StockStatus.fromQuantity(1), StockStatus.lowStock);
      expect(StockStatus.fromQuantity(5), StockStatus.lowStock);
      expect(StockStatus.fromQuantity(6), StockStatus.inStock);
    });

    test('labels match the UI copy', () {
      expect(StockStatus.inStock.label, 'In stock');
      expect(StockStatus.lowStock.label, 'Low stock');
      expect(StockStatus.outOfStock.label, 'Out of stock');
    });
  });

  group('ProductDetail', () {
    test('parses the OpenAPI ProductDetail shape', () {
      final p = ProductDetail.fromJson(_detailJson());
      expect(p.priceMinor, 8999);
      expect(p.salePriceMinor, 6999);
      expect(p.stockStatus, StockStatus.lowStock);
      expect(p.category.slug, 'pendant-lights');
      expect(p.specifications.wattageW, 9);
      expect(p.specifications.dimensionsMm?.diameterMm, 300);
      expect(p.specifications.lumens, isNull);
      expect(p.isOnSale, isTrue);
      expect(p.effectivePriceMinor, 6999);
    });

    test('effective price falls back to the regular price', () {
      final p = ProductDetail.fromJson(_detailJson(salePriceMinor: null));
      expect(p.isOnSale, isFalse);
      expect(p.effectivePriceMinor, 8999);
    });

    test('json round trip omits null specification fields', () {
      final p = ProductDetail.fromJson(_detailJson());
      final json = p.toJson();
      final specs = json['specifications'] as Map<String, dynamic>;
      expect(specs.containsKey('lumens'), isFalse);
      expect(specs['dimensionsMm'], {'heightMm': 220, 'diameterMm': 300});
      expect(json['stockStatus'], 'low_stock');
      expect(json.containsKey('salePriceMinor'), isTrue);
      expect(ProductDetail.fromJson(json), p);
    });

    test('rejects keys that are not in the contract', () {
      final json = _detailJson()..['colour'] = 'red';
      expect(() => ProductDetail.fromJson(json), throwsA(anything));
    });

    test('is immutable with value equality', () {
      final a = ProductDetail.fromJson(_detailJson());
      final b = a.copyWith(stockQuantity: 10);
      expect(a.stockQuantity, 4);
      expect(b.stockQuantity, 10);
      expect(a, ProductDetail.fromJson(_detailJson()));
      expect(a == b, isFalse);
    });

    test('toSummary projects list fields', () {
      final p = ProductDetail.fromJson(_detailJson());
      final s = p.toSummary();
      expect(s.id, p.id);
      expect(s.name, p.name);
      expect(s.priceMinor, p.priceMinor);
      expect(s.salePriceMinor, p.salePriceMinor);
      expect(s.stockStatus, p.stockStatus);
      expect(s.imageAlt, p.imageAlt);
      expect(s.effectivePriceMinor, 6999);
    });
  });
}
