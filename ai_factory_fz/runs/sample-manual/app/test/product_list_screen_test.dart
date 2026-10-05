// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease/models.dart';
import 'package:shopease/providers.dart';
import 'package:shopease/screens/product_list_screen.dart';

const shoe = Product(id: 'p1', name: 'Shoe', priceCents: 5900, imageUrl: 'http://localhost/shoe.png', description: 'A shoe');

Widget app(Future<List<Product>> Function() load) => ProviderScope(
      overrides: [productsProvider.overrideWith((ref) => load())],
      child: const MaterialApp(home: ProductListScreen()),
    );

void main() {
  testWidgets('shows name and price for each product (US-001)', (tester) async {
    await tester.pumpWidget(app(() async => [shoe]));
    await tester.pumpAndSettle();
    expect(find.text('Shoe'), findsOneWidget);
    expect(find.text('\$59.00'), findsOneWidget);
  });

  testWidgets('shows a loading state while the API has not answered (US-001)', (tester) async {
    await tester.pumpWidget(app(() => Future.delayed(const Duration(seconds: 1), () => [shoe])));
    await tester.pump();
    expect(find.text('Loading products'), findsOneWidget);
    await tester.pumpAndSettle();
  });

  testWidgets('shows the empty state when there are no products (US-001)', (tester) async {
    await tester.pumpWidget(app(() async => []));
    await tester.pumpAndSettle();
    expect(find.text('No products yet. Check back soon.'), findsOneWidget);
  });

  testWidgets('shows an error with a retry button when loading fails', (tester) async {
    await tester.pumpWidget(app(() async => throw Exception('boom')));
    await tester.pumpAndSettle();
    expect(find.text("We couldn't load products."), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });
}
