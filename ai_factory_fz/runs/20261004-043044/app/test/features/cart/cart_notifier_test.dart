import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shopease_app/features/cart/presentation/cart_notifier.dart';
import '../../helpers/catalog_test_overrides.dart';
import 'package:shopease_app/features/catalog/domain/models/product.dart';
import 'package:shopease_app/features/catalog/domain/models/product_variant.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_notifier.dart';

void main() {
  const productId = 'p1111111-1111-4111-8111-111111111101';
  const inStockVariantId = 'v1111111-1111-4111-8111-111111111101';
  const oosVariantId = 'v1111111-1111-4111-8111-111111111102';

  ProviderContainer buildContainer() {
    return ProviderContainer(
      overrides: localCatalogOverrides(),
    );
  }

  Future<({ProductDetail product, ProductVariant variant})> loadDefaultVariant(
    ProviderContainer container,
  ) async {
    final data = await container.read(
      productDetailNotifierProvider(productId).future,
    );
    final variant = data.selectedVariant!;
    return (product: data.product, variant: variant);
  }

  test('addFromVariant snapshots name, label, price and quantity one', () async {
    final container = buildContainer();
    addTearDown(container.dispose);

    final loaded = await loadDefaultVariant(container);
    container.read(cartNotifierProvider.notifier).addFromVariant(
          product: loaded.product,
          variant: loaded.variant,
        );

    final state = container.read(cartNotifierProvider);
    expect(state.lineItemCount, 1);
    final line = state.items[inStockVariantId]!;
    expect(line.productName, 'Modern LED Ceiling Light');
    expect(line.variantLabel, loaded.variant.label);
    expect(line.unitPriceCents, loaded.variant.price.priceMinorUnits);
    expect(line.currency, 'GBP');
    expect(line.quantity, 1);
    expect(state.subtotalCents, line.unitPriceCents);
  });

  test('merge-on-add increments quantity for same variant', () async {
    final container = buildContainer();
    addTearDown(container.dispose);
    final loaded = await loadDefaultVariant(container);
    final notifier = container.read(cartNotifierProvider.notifier);

    notifier.addFromVariant(product: loaded.product, variant: loaded.variant);
    notifier.addFromVariant(product: loaded.product, variant: loaded.variant);

    final state = container.read(cartNotifierProvider);
    expect(state.lineItemCount, 1);
    expect(state.items[inStockVariantId]!.quantity, 2);
    expect(
      state.subtotalCents,
      state.items[inStockVariantId]!.unitPriceCents * 2,
    );
  });

  test('does not add out-of-stock variant', () async {
    final container = buildContainer();
    addTearDown(container.dispose);

    await container.read(productDetailNotifierProvider(productId).future);
    container
        .read(productDetailNotifierProvider(productId).notifier)
        .selectVariant(oosVariantId);
    final updated = container.read(productDetailNotifierProvider(productId)).requireValue;
    final oosVariant = updated.selectedVariant!;

    container.read(cartNotifierProvider.notifier).addFromVariant(
          product: updated.product,
          variant: oosVariant,
        );

    expect(container.read(cartNotifierProvider).isEmpty, isTrue);
  });

  test('quantity updates and remove recalculate subtotal', () async {
    final container = buildContainer();
    addTearDown(container.dispose);
    final loaded = await loadDefaultVariant(container);
    final notifier = container.read(cartNotifierProvider.notifier);
    final unit = loaded.variant.price.priceMinorUnits;

    notifier.addFromVariant(product: loaded.product, variant: loaded.variant);
    notifier.setQuantity(inStockVariantId, 3);
    expect(container.read(cartNotifierProvider).subtotalCents, unit * 3);

    notifier.decrementQuantity(inStockVariantId);
    expect(container.read(cartNotifierProvider).subtotalCents, unit * 2);

    notifier.removeLine(inStockVariantId);
    expect(container.read(cartNotifierProvider).isEmpty, isTrue);
  });
}
