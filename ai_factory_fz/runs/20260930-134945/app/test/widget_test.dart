import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_screen.dart';

Widget _app({GoRouter? router}) => ProviderScope(
  overrides: [if (router != null) appRouterProvider.overrideWithValue(router)],
  child: const LightingShopApp(),
);

void main() {
  testWidgets('app launches on the Product List route', (tester) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    expect(find.byType(ProductListScreen), findsOneWidget);
    expect(find.text('Lighting'), findsOneWidget);
    expect(find.text('No products available'), findsOneWidget);
  });

  testWidgets('cart button opens Cart and back returns to list', (
    tester,
  ) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Cart'));
    await tester.pumpAndSettle();
    expect(find.byType(CartScreen), findsOneWidget);
    expect(find.text('Your cart is empty'), findsOneWidget);

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('empty cart Browse products goes to list', (tester) async {
    final router = buildAppRouter(initialLocation: '/cart');
    addTearDown(router.dispose);
    await tester.pumpWidget(_app(router: router));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Browse products'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('pushNamed productDetail receives productId and pops to list', (
    tester,
  ) async {
    final router = buildAppRouter();
    addTearDown(router.dispose);
    await tester.pumpWidget(_app(router: router));
    await tester.pumpAndSettle();

    router.pushNamed(
      AppRoutes.productDetail,
      pathParameters: {AppRoutes.productIdParam: 'abc-123'},
    );
    await tester.pumpAndSettle();

    final detail = tester.widget<ProductDetailScreen>(
      find.byType(ProductDetailScreen),
    );
    expect(detail.productId, 'abc-123');

    await tester.pageBack();
    await tester.pumpAndSettle();
    expect(find.byType(ProductDetailScreen), findsNothing);
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  test('named routes resolve to the spec paths', () {
    final router = buildAppRouter();
    addTearDown(router.dispose);
    expect(router.namedLocation(AppRoutes.productList), '/');
    expect(
      router.namedLocation(
        AppRoutes.productDetail,
        pathParameters: {AppRoutes.productIdParam: 'p1'},
      ),
      '/products/p1',
    );
    expect(router.namedLocation(AppRoutes.cart), '/cart');
  });

  testWidgets('deep link to unknown product shows not found with back action', (
    tester,
  ) async {
    final router = buildAppRouter(initialLocation: '/products/unknown');
    addTearDown(router.dispose);
    await tester.pumpWidget(_app(router: router));
    await tester.pumpAndSettle();

    expect(find.text('Product not found'), findsOneWidget);
    await tester.tap(find.text('Back to products'));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('cart button meets 48dp minimum touch target', (tester) async {
    await tester.pumpWidget(_app());
    await tester.pumpAndSettle();
    final size = tester.getSize(find.byType(IconButton));
    expect(size.width, greaterThanOrEqualTo(48));
    expect(size.height, greaterThanOrEqualTo(48));
  });
}
