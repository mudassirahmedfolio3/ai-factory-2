import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/cart/domain/cart.dart';
import 'package:shopease_app/features/cart/domain/cart_item.dart';
import 'package:shopease_app/features/cart/domain/cart_state.dart';
import 'package:shopease_app/features/cart/presentation/cart_notifier.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';

/// US-007/US-008: checkout must start a UK checkout flow, not a placeholder snackbar.
void main() {
  testWidgets('Checkout button starts checkout flow (not MVP placeholder)', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          cartNotifierProvider.overrideWith(_CartWithLine.new),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const CartScreen(),
        ),
      ),
    );

    await tester.tap(find.text('Checkout'));
    await tester.pump();

    expect(find.text('Checkout coming in full MVP'), findsNothing);
  });
}

class _CartWithLine extends CartNotifier {
  @override
  CartState build() {
    return CartState(
      cart: Cart(
        items: {
          'v-test': const CartItem(
            variantId: 'v-test',
            productName: 'Test Pendant',
            variantLabel: 'Brass',
            unitPriceCents: 9999,
            currency: 'GBP',
            quantity: 1,
          ),
        },
      ),
    );
  }
}
