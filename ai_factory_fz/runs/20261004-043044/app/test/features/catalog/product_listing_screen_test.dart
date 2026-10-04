import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/widgets/out_of_stock_badge.dart';
import 'package:shopease_app/core/widgets/product_card.dart';

import '../../helpers/catalog_test_overrides.dart';

void main() {
  testWidgets('Product listing shows seeded product cards', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.tap(find.text('Products'));
    await pumpUntilSettled(tester);

    expect(find.byType(ProductCard), findsWidgets);
    expect(find.textContaining('£'), findsWidgets);
  });

  testWidgets('Inline search filters products and empty state clears', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.tap(find.text('Products'));
    await pumpUntilSettled(tester);

    await tester.enterText(
      find.bySemanticsLabel('Product search'),
      'no-such-product-xyz',
    );
    await tester.pump(const Duration(milliseconds: 350));
    await pumpUntilSettled(tester);

    expect(find.text('No products match your search'), findsOneWidget);

    await tester.tap(find.text('Clear search'));
    await pumpUntilSettled(tester);

    expect(find.byType(ProductCard), findsWidgets);
  });

  testWidgets('Fully out-of-stock seeded product shows Out of stock badge', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.tap(find.text('Products'));
    await pumpUntilSettled(tester);

    await tester.enterText(
      find.bySemanticsLabel('Product search'),
      'Garden Bollard Light',
    );
    await tester.pump(const Duration(milliseconds: 350));
    await pumpUntilSettled(tester);

    expect(find.byType(ProductCard), findsOneWidget);
    expect(find.byType(OutOfStockBadge), findsOneWidget);
  });

  testWidgets('Category navigation from home filters listing', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(overrides: catalogTestOverrides, child: const LumenApp()),
    );
    await pumpUntilSettled(tester);

    await tester.tap(find.text('Ceiling Lights'));
    await pumpUntilSettled(tester);

    expect(find.text('Modern LED Ceiling Light'), findsOneWidget);
    expect(find.text('Products'), findsWidgets);
  });
}
