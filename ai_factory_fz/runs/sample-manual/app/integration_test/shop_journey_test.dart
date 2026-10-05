// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
// On-device journeys using Flutter's integration_test package. They drive the real app against the staging API
// (no mocked network). Every test starts from a fresh app and empties the cart first, so tests do not depend on each other.
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shopease/main.dart' as app;

Future<void> launch(WidgetTester tester) async {
  app.main();
  await tester.pumpAndSettle(const Duration(seconds: 5));
}

/// Opens the first product and returns its name and price text so tests can assert on them later.
Future<({String name, String price})> openFirstProduct(WidgetTester tester) async {
  final card = find.byType(InkWell).first;
  final texts = tester.widgetList<Text>(find.descendant(of: card, matching: find.byType(Text))).map((t) => t.data!).toList();
  await tester.tap(card);
  await tester.pumpAndSettle();
  return (name: texts[0], price: texts[1]);
}

Future<void> emptyCart(WidgetTester tester) async {
  await tester.tap(find.text('Cart'));
  await tester.pumpAndSettle();
  while (find.byIcon(Icons.remove).evaluate().isNotEmpty) {
    await tester.tap(find.byIcon(Icons.remove).first);
    await tester.pumpAndSettle();
  }
  await tester.tap(find.text('Shop'));
  await tester.pumpAndSettle();
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('browse, open a product and add it: the cart shows that product with quantity 1 and its price', (tester) async {
    await launch(tester);
    await emptyCart(tester);
    final product = await openFirstProduct(tester);
    expect(find.text(product.name), findsOneWidget);
    expect(find.text(product.price), findsOneWidget);
    await tester.tap(find.text('Add to cart'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cart'));
    await tester.pumpAndSettle();
    expect(find.text(product.name), findsOneWidget);
    expect(find.textContaining('x 1 = ${product.price}'), findsOneWidget);
    expect(find.text('Total: ${product.price}'), findsOneWidget);
  });

  testWidgets('adding the same product twice and then changing the quantity updates line total and cart total', (tester) async {
    await launch(tester);
    await emptyCart(tester);
    final product = await openFirstProduct(tester);
    await tester.tap(find.text('Add to cart'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Add to cart'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cart'));
    await tester.pumpAndSettle();
    expect(find.textContaining('x 2 ='), findsOneWidget);
    await tester.tap(find.byIcon(Icons.remove).first);
    await tester.pumpAndSettle();
    expect(find.textContaining('x 1 = ${product.price}'), findsOneWidget);
    expect(find.text('Total: ${product.price}'), findsOneWidget);
  });

  testWidgets('an empty cart shows the empty-state message', (tester) async {
    await launch(tester);
    await emptyCart(tester);
    await tester.tap(find.text('Cart'));
    await tester.pumpAndSettle();
    expect(find.text('Your cart is empty. Browse products to add some.'), findsOneWidget);
  });
}
