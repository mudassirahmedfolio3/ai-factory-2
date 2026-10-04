import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import 'package:shopease_app/features/cart/presentation/cart_controller.dart';
import '../../../support/fixed_auth_notifier.dart';

void main() {
  ProviderContainer testContainer() {
    return ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestCartStorageProvider.overrideWithValue(
          InMemoryGuestCartLocalRepository(),
        ),
      ],
    );
  }

  test(
    'adds, increments, decrements, and removes cart lines with guest persistence',
    () async {
      final container = testContainer();
      addTearDown(container.dispose);

      await container.read(cartControllerProvider.future);
      final controller = container.read(cartControllerProvider.notifier);

      await controller.addProduct(
        productId: 'product-1',
        productName: 'Citrus Hand Soap',
        variantId: 'variant-300',
        variantName: '300 ml',
        unitPriceCents: 799,
        currencyCode: 'USD',
        maxQuantity: 10,
      );
      await controller.addProduct(
        productId: 'product-1',
        productName: 'Citrus Hand Soap',
        variantId: 'variant-300',
        variantName: '300 ml',
        unitPriceCents: 799,
        currencyCode: 'USD',
        maxQuantity: 10,
      );

      var state = container.read(cartControllerProvider).value!;
      expect(state.lines, hasLength(1));
      expect(state.itemCount, 2);
      expect(state.subtotalCents, 1598);

      final lineId = state.lines.first.id;
      await controller.incrementLine(lineId);
      state = container.read(cartControllerProvider).value!;
      expect(state.lines.first.quantity, 3);
      expect(state.subtotalCents, 2397);

      await controller.decrementLine(lineId);
      state = container.read(cartControllerProvider).value!;
      expect(state.lines.first.quantity, 2);

      await controller.decrementLine(lineId);
      await controller.decrementLine(lineId);
      state = container.read(cartControllerProvider).value!;
      expect(state.lines, isEmpty);
      expect(state.itemCount, 0);
      expect(state.subtotalCents, 0);
    },
  );

  test('blocks add and increment when out of stock or over max quantity', () async {
    final container = testContainer();
    addTearDown(container.dispose);

    await container.read(cartControllerProvider.future);
    final controller = container.read(cartControllerProvider.notifier);

    final blocked = await controller.addProduct(
      productId: 'product-1',
      productName: 'Sold out soap',
      variantId: 'variant-oos',
      variantName: '300 ml',
      unitPriceCents: 799,
      currencyCode: 'USD',
      isAvailable: false,
    );
    expect(blocked, CartAddResult.outOfStock);

    await controller.addProduct(
      productId: 'product-2',
      productName: 'Limited soap',
      variantId: 'variant-limited',
      variantName: '300 ml',
      unitPriceCents: 799,
      currencyCode: 'USD',
      maxQuantity: 1,
    );
    final secondAdd = await controller.addProduct(
      productId: 'product-2',
      productName: 'Limited soap',
      variantId: 'variant-limited',
      variantName: '300 ml',
      unitPriceCents: 799,
      currencyCode: 'USD',
      maxQuantity: 1,
    );
    expect(secondAdd, CartAddResult.outOfStock);

    final lineId = container.read(cartControllerProvider).value!.lines.first.id;
    final increment = await controller.incrementLine(lineId);
    expect(increment, CartQuantityResult.outOfStock);
  });

  test('starts a new guest session with isolated cart state', () async {
    final container = testContainer();
    addTearDown(container.dispose);

    final initial = await container.read(cartControllerProvider.future);
    final controller = container.read(cartControllerProvider.notifier);
    final firstSessionId = initial.guestSessionId;

    await controller.addProduct(
      productId: 'product-2',
      productName: 'Aroma Candle',
      variantId: 'variant-standard',
      variantName: 'Standard',
      unitPriceCents: 2499,
      currencyCode: 'USD',
    );
    expect(container.read(cartControllerProvider).value!.itemCount, 1);

    await controller.startNewGuestSession();
    final renewed = container.read(cartControllerProvider).value!;
    expect(renewed.guestSessionId, isNot(firstSessionId));
    expect(renewed.lines, isEmpty);
  });
}
