import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/cart/domain/cart.dart';
import 'package:shopease_app/features/cart/domain/cart_item.dart';
import 'package:shopease_app/features/cart/domain/cart_state.dart';
import 'package:shopease_app/features/cart/presentation/cart_notifier.dart';
import 'package:shopease_app/features/catalog/presentation/filter_sort_bottom_sheet.dart';

import '../../helpers/catalog_test_overrides.dart';

void main() {
  testWidgets('AppShell shows Home, Products, and Cart destinations', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Products'), findsOneWidget);
    expect(find.text('Cart'), findsOneWidget);
    expect(find.text('Account'), findsOneWidget);
    expect(find.text('Flutter Demo'), findsNothing);
  });

  testWidgets('AppShell navigates between tabs', (WidgetTester tester) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.tap(find.text('Products'));
    await pumpUntilSettled(tester);
    expect(find.text('Filters'), findsOneWidget);

    await tester.tap(find.text('Cart'));
    await pumpUntilSettled(tester);
    expect(find.text('Your cart is empty'), findsOneWidget);

    await tester.tap(find.text('Home'));
    await pumpUntilSettled(tester);
    expect(find.text('Shop by room'), findsOneWidget);
  });

  testWidgets('Cart tab badge reflects line item count', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          ...catalogTestOverrides,
          cartNotifierProvider.overrideWith(_CartWithTwoItems.new),
        ],
        child: const LumenApp(),
      ),
    );
    await pumpUntilSettled(tester);

    expect(find.text('2'), findsWidgets);
  });

  testWidgets('FilterSortBottomSheet opens as modal not route', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: catalogTestOverrides,
        child: MaterialApp(
          theme: AppTheme.light(),
          home: Builder(
            builder: (context) {
              return Scaffold(
                body: Center(
                  child: ElevatedButton(
                    onPressed: () => FilterSortBottomSheet.show(context),
                    child: const Text('Open filters'),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('Open filters'));
    await tester.pumpAndSettle();

    expect(find.text('Filters and sort'), findsOneWidget);
    expect(find.text('Apply filters'), findsOneWidget);
  });
}

class _CartWithTwoItems extends CartNotifier {
  @override
  CartState build() {
    return CartState(
      cart: Cart(
        items: {
          'v1': const CartItem(
            variantId: 'v1',
            productName: 'Line one',
            variantLabel: 'A',
            unitPriceCents: 1000,
            currency: 'GBP',
            quantity: 1,
          ),
          'v2': const CartItem(
            variantId: 'v2',
            productName: 'Line two',
            variantLabel: 'B',
            unitPriceCents: 2000,
            currency: 'GBP',
            quantity: 1,
          ),
        },
      ),
    );
  }
}
