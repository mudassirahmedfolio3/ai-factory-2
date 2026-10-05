// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease/models.dart';
import 'package:shopease/providers.dart';
import 'package:shopease/screens/cart_screen.dart';

class FakeCart extends CartNotifier {
  FakeCart(this._cart);
  Cart _cart;

  @override
  Future<Cart> build() async => _cart;

  @override
  Future<void> setQuantity(String productId, int quantity) async {
    final items = [
      for (final i in _cart.items)
        if (i.productId != productId)
          i
        else if (quantity > 0)
          CartItem(productId: i.productId, name: i.name, unitPriceCents: i.unitPriceCents, quantity: quantity, lineTotalCents: i.unitPriceCents * quantity),
    ];
    _cart = Cart(items: items, totalCents: items.fold(0, (s, i) => s + i.lineTotalCents));
    state = AsyncData(_cart);
  }
}

const shoe = CartItem(productId: 'p1', name: 'Shoe', unitPriceCents: 5900, quantity: 2, lineTotalCents: 11800);

Widget app(Cart cart) => ProviderScope(
      overrides: [cartProvider.overrideWith(() => FakeCart(cart))],
      child: const MaterialApp(home: CartScreen()),
    );

void main() {
  testWidgets('empty cart shows the empty state (US-004)', (tester) async {
    await tester.pumpWidget(app(const Cart(items: [], totalCents: 0)));
    await tester.pumpAndSettle();
    expect(find.text('Your cart is empty. Browse products to add some.'), findsOneWidget);
  });

  testWidgets('each line shows name, unit price, quantity and line total, plus the cart total (US-004)', (tester) async {
    await tester.pumpWidget(app(const Cart(items: [shoe], totalCents: 11800)));
    await tester.pumpAndSettle();
    expect(find.text('Shoe'), findsOneWidget);
    expect(find.text('\$59.00 x 2 = \$118.00'), findsOneWidget);
    expect(find.text('Total: \$118.00'), findsOneWidget);
  });

  testWidgets('changing a quantity recalculates the line and the total (US-004)', (tester) async {
    await tester.pumpWidget(app(const Cart(items: [shoe], totalCents: 11800)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('minus-p1')));
    await tester.pumpAndSettle();
    expect(find.text('\$59.00 x 1 = \$59.00'), findsOneWidget);
    expect(find.text('Total: \$59.00'), findsOneWidget);
  });
}
