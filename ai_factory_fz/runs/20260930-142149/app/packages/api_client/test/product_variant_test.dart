import 'package:test/test.dart';
import 'package:api_client/api_client.dart';

// tests for ProductVariant
void main() {
  final instance = ProductVariantBuilder();
  // TODO add properties to the builder and call build()

  group(ProductVariant, () {
    // String id
    test('to test the property `id`', () async {
      // TODO
    });

    // String sku
    test('to test the property `sku`', () async {
      // TODO
    });

    // String name
    test('to test the property `name`', () async {
      // TODO
    });

    // Exactly one variant per product is the default.
    // bool isDefault
    test('to test the property `isDefault`', () async {
      // TODO
    });

    // BuiltList<VariantOption> options
    test('to test the property `options`', () async {
      // TODO
    });

    // Money price
    test('to test the property `price`', () async {
      // TODO
    });

    // Sale price actually charged when on sale; null when not on sale. Must be lower than price.
    // Money salePrice
    test('to test the property `salePrice`', () async {
      // TODO
    });

    // int stockQuantity
    test('to test the property `stockQuantity`', () async {
      // TODO
    });

    // Image image
    test('to test the property `image`', () async {
      // TODO
    });

    // Non-null fields replace the product specifications for this variant; null when the variant has no overrides.
    // LightingSpecifications specificationOverrides
    test('to test the property `specificationOverrides`', () async {
      // TODO
    });

  });
}
