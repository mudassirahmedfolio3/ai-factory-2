import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/cart/presentation/cart_notifier.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_screen.dart';

import '../../helpers/catalog_test_overrides.dart';

const _productId = 'p1111111-1111-4111-8111-111111111101';

Future<void> pumpProductDetail(WidgetTester tester) async {
  final container = ProviderContainer(overrides: catalogTestOverrides);
  addTearDown(container.dispose);

  await tester.pumpWidget(
    UncontrolledProviderScope(
      container: container,
      child: MaterialApp(home: ProductDetailScreen(productId: _productId)),
    ),
  );
  for (var i = 0; i < 30; i++) {
    await tester.pump(const Duration(milliseconds: 100));
    if (find.text('Add to cart').evaluate().isNotEmpty ||
        find.text('Out of stock').evaluate().isNotEmpty) {
      break;
    }
  }
}

void main() {
  testWidgets('Product detail shows specs, variants, and reviews preview', (
    WidgetTester tester,
  ) async {
    await pumpProductDetail(tester);

    expect(find.textContaining('CL-1001-WH'), findsWidgets);
    expect(find.text('Wattage'), findsOneWidget);
    expect(find.text('24W'), findsOneWidget);
    expect(find.text('IP44'), findsOneWidget);
    expect(find.text('Bright and easy fit'), findsOneWidget);
    expect(find.text('Add to cart'), findsOneWidget);
  });

  testWidgets('Add to cart adds snapshot line with quantity one', (
    WidgetTester tester,
  ) async {
    final container = ProviderContainer(overrides: catalogTestOverrides);
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(home: ProductDetailScreen(productId: _productId)),
      ),
    );
    for (var i = 0; i < 30; i++) {
      await tester.pump(const Duration(milliseconds: 100));
      if (find.text('Add to cart').evaluate().isNotEmpty) {
        break;
      }
    }

    await tester.tap(find.text('Add to cart'));
    await tester.pump();

    final cart = container.read(cartNotifierProvider);
    expect(cart.lineItemCount, 1);
    expect(cart.lines.single.productName, 'Modern LED Ceiling Light');
    expect(cart.lines.single.quantity, 1);
  });

  testWidgets('Selecting out-of-stock variant disables add to cart', (
    WidgetTester tester,
  ) async {
    await pumpProductDetail(tester);

    final variantChip = find.textContaining('Matte Black');
    await tester.ensureVisible(variantChip);
    await tester.tap(variantChip);
    await tester.pump();

    expect(find.textContaining('CL-1001-BK'), findsWidgets);
    expect(find.widgetWithText(FilledButton, 'Out of stock'), findsOneWidget);
  });
}
