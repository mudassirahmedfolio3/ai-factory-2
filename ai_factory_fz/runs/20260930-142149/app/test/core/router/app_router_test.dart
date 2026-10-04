import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_screen.dart';

Future<GoRouter> _pumpRouter(WidgetTester tester, {String? initial}) async {
  final router = buildAppRouter(
    initialLocation: initial ?? AppRoutes.initialLocation,
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [appRouterProvider.overrideWithValue(router)],
      child: MaterialApp.router(theme: AppTheme.light, routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
  return router;
}

void main() {
  test('productDetail builds an encoded child location', () {
    expect(AppRoutes.productDetail('prd_001'), '/products/prd_001');
    expect(AppRoutes.productDetail('a b'), '/products/a%20b');
  });

  testWidgets('initial location is the product list', (tester) async {
    await _pumpRouter(tester);
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('/ redirects to /products', (tester) async {
    await _pumpRouter(tester, initial: '/');
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('detail is a child route: list stays beneath, back pops to it', (
    tester,
  ) async {
    final router = await _pumpRouter(tester);
    router.go(AppRoutes.productDetail('prd_001'));
    await tester.pumpAndSettle();

    final detail = tester.widget<ProductDetailScreen>(
      find.byType(ProductDetailScreen),
    );
    expect(detail.productId, 'prd_001');
    // List remains mounted offstage in the navigator stack.
    expect(find.byType(ProductListScreen, skipOffstage: false), findsOneWidget);
    expect(router.canPop(), isTrue);

    router.pop();
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
    expect(find.byType(ProductDetailScreen), findsNothing);
  });

  testWidgets('detail not-found state goes back to products', (tester) async {
    await _pumpRouter(tester, initial: AppRoutes.productDetail('missing'));
    expect(find.text('Product not found'), findsOneWidget);

    await tester.tap(find.text('Back to products'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('cart is pushed on top and Browse products returns to list', (
    tester,
  ) async {
    final router = await _pumpRouter(tester);
    router.push(AppRoutes.cartPath);
    await tester.pumpAndSettle();

    expect(find.byType(CartScreen), findsOneWidget);
    expect(find.text('Your cart is empty'), findsOneWidget);

    await tester.tap(find.text('Browse products'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
    expect(find.byType(CartScreen), findsNothing);
  });

  testWidgets('unknown location falls back to the product list', (
    tester,
  ) async {
    await _pumpRouter(tester, initial: '/does-not-exist');
    expect(find.byType(ProductListScreen), findsOneWidget);
  });
}
