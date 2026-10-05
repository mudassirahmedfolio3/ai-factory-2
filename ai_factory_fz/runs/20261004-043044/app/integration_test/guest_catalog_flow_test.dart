import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shopease_app/app.dart';

import '../test/helpers/catalog_test_overrides.dart';

/// Guest journey SCR-01 → SCR-02 → SCR-03 → SCR-04 → SCR-05 with local catalog.
/// Run: scripts/run-guest-catalog-integration.ps1 (in-memory seed; API not required).
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  Future<void> pumpUntil(
    WidgetTester tester,
    Finder finder, {
    int maxFrames = 60,
  }) async {
    for (var i = 0; i < maxFrames; i++) {
      await tester.pump(const Duration(milliseconds: 100));
      if (finder.evaluate().isNotEmpty) {
        return;
      }
    }
    fail('Timed out waiting for ${finder.describeMatch(Plurality.one)}');
  }

  testWidgets('home → listing → detail → reviews → cart (local fallback)', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: catalogTestOverrides,
        child: const LumenApp(),
      ),
    );
    await pumpUntil(tester, find.text('Shop by room'));

    await tester.tap(find.byTooltip('Browse products'));
    await pumpUntil(tester, find.byKey(const Key('product-listing-grid')));

    final productCard = find.text('Modern LED Ceiling Light');
    await tester.ensureVisible(productCard.first);
    await tester.tap(productCard.first);
    await pumpUntil(tester, find.text('Add to cart'));

    expect(find.textContaining('CL-1001-WH'), findsWidgets);
    expect(find.text('Specifications'), findsOneWidget);

    await tester.ensureVisible(find.text('2 reviews'));
    await tester.tap(find.text('2 reviews'));
    await pumpUntil(tester, find.text('Reviews'));

    expect(find.text('Bright and easy fit'), findsOneWidget);
    expect(
      find.textContaining('Installed in our kitchen'),
      findsOneWidget,
    );

    await tester.tap(find.bySemanticsLabel('Go back'));
    await pumpUntil(tester, find.text('Add to cart'));

    await tester.tap(find.text('Add to cart'));
    await pumpUntil(tester, find.text('View cart'));
    await tester.tap(find.text('View cart'));
    await pumpUntil(tester, find.text('Your cart'));

    expect(find.text('Modern LED Ceiling Light'), findsOneWidget);
    expect(find.text('£49.99'), findsWidgets);
  });
}
