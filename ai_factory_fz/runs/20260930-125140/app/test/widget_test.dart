import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/app.dart';
import 'package:shopease_app/core/l10n/app_strings.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/core/router/app_routes.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_detail_screen.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_screen.dart';

Future<GoRouter> pumpApp(WidgetTester tester, {String? initialLocation}) async {
  final router = buildAppRouter(
    initialLocation: initialLocation ?? AppRoutes.productList,
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [appRouterProvider.overrideWithValue(router)],
      child: const ShopEaseApp(),
    ),
  );
  await tester.pumpAndSettle();
  return router;
}

void main() {
  testWidgets('app launches on the product list route', (tester) async {
    await pumpApp(tester);
    expect(find.byType(ProductListScreen), findsOneWidget);
    expect(find.text(AppStrings.productListTitle), findsOneWidget);
  });

  testWidgets('cart icon pushes /cart and back pops to the list', (
    tester,
  ) async {
    final router = await pumpApp(tester);
    await tester.tap(find.bySemanticsLabel(AppStrings.cartTitle).first);
    await tester.pumpAndSettle();
    expect(find.byType(CartScreen), findsOneWidget);
    expect(find.text(AppStrings.emptyCart), findsOneWidget);

    router.pop();
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('empty cart Browse products goes to the list', (tester) async {
    await pumpApp(tester, initialLocation: AppRoutes.cart);
    await tester.tap(find.text(AppStrings.browseProducts));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('detail route receives the productId path parameter', (
    tester,
  ) async {
    final router = await pumpApp(tester);
    router.push(AppRoutes.productDetailLocation('abc-123'));
    await tester.pumpAndSettle();
    final screen = tester.widget<ProductDetailScreen>(
      find.byType(ProductDetailScreen),
    );
    expect(screen.productId, 'abc-123');

    await tester.tap(find.text(AppStrings.backToList));
    await tester.pumpAndSettle();
    expect(find.byType(ProductListScreen), findsOneWidget);
  });

  testWidgets('unknown routes show the not-found state', (tester) async {
    await pumpApp(tester, initialLocation: '/does-not-exist');
    expect(find.text(AppStrings.pageNotFound), findsOneWidget);
  });

  testWidgets('interactive elements meet the 48dp tap target guideline', (
    tester,
  ) async {
    final handle = tester.ensureSemantics();
    await pumpApp(tester, initialLocation: AppRoutes.cart);
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    handle.dispose();
  });

  testWidgets('app follows the system theme mode', (tester) async {
    await pumpApp(tester);
    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.themeMode, ThemeMode.system);
    expect(app.darkTheme, isNotNull);
  });
}
