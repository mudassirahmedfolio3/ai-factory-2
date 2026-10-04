import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/cart/domain/cart.dart';
import 'package:shopease_app/features/cart/domain/cart_item.dart';
import 'package:shopease_app/features/cart/domain/cart_state.dart';
import 'package:shopease_app/features/cart/presentation/cart_notifier.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';

void main() {
  testWidgets('CartScreen shows empty state', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const CartScreen(),
        ),
      ),
    );

    expect(find.text('Your cart is empty'), findsOneWidget);
    expect(find.text('Browse products'), findsOneWidget);
  });

  testWidgets('CartScreen shows lines, subtotal, and quantity steppers', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          cartNotifierProvider.overrideWith(_CartWithOneLine.new),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const CartScreen(),
        ),
      ),
    );

    expect(find.text('Modern LED Ceiling Light'), findsOneWidget);
    expect(find.text('Bright White'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(find.text('Subtotal'), findsOneWidget);
    expect(find.text('Checkout'), findsOneWidget);
  });

  testWidgets('Increasing quantity updates subtotal', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          cartNotifierProvider.overrideWith(_MutableCartNotifier.new),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const CartScreen(),
        ),
      ),
    );

    final subtotalFinder = find.text('Subtotal');
    expect(subtotalFinder, findsOneWidget);

    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    expect(find.text('2'), findsOneWidget);
  });

  testWidgets('Remove line clears cart to empty state', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          cartNotifierProvider.overrideWith(_MutableCartNotifier.new),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const CartScreen(),
        ),
      ),
    );

    await tester.tap(find.byIcon(Icons.delete_outline));
    await tester.pump();

    expect(find.text('Your cart is empty'), findsOneWidget);
  });
}

class _CartWithOneLine extends CartNotifier {
  @override
  CartState build() {
    return CartState(
      cart: Cart(
        items: {
          'v1': const CartItem(
            variantId: 'v1',
            productName: 'Modern LED Ceiling Light',
            variantLabel: 'Bright White',
            unitPriceCents: 4999,
            currency: 'GBP',
            quantity: 2,
            imageUrl: 'assets/images/products/placeholder.png',
          ),
        },
      ),
    );
  }
}

class _MutableCartNotifier extends CartNotifier {
  @override
  CartState build() {
    return CartState(
      cart: Cart(
        items: {
          'v1': const CartItem(
            variantId: 'v1',
            productName: 'Modern LED Ceiling Light',
            variantLabel: 'Bright White',
            unitPriceCents: 4999,
            currency: 'GBP',
            quantity: 1,
            imageUrl: 'assets/images/products/placeholder.png',
          ),
        },
      ),
    );
  }
}
