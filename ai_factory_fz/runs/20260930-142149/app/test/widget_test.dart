import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:shopease_app/app.dart';
import 'package:shopease_app/features/catalog/presentation/product_list_screen.dart';

void main() {
  testWidgets('app launches offline straight to the product list', (
    tester,
  ) async {
    await tester.pumpWidget(const ProviderScope(child: LightingShopApp()));
    await tester.pumpAndSettle();

    expect(find.byType(ProductListScreen), findsOneWidget);
    expect(find.text(ProductListScreen.title), findsOneWidget);
    // No sign-in prompt anywhere on launch.
    expect(find.textContaining('Sign in'), findsNothing);
    expect(find.textContaining('Log in'), findsNothing);
  });

  testWidgets('app uses the token-based light and dark themes', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: LightingShopApp()));
    await tester.pumpAndSettle();

    final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
    expect(app.theme?.colorScheme.primary, const Color(0xFF1A5FB4));
    expect(app.darkTheme?.colorScheme.primary, const Color(0xFFA8C7FA));
    expect(app.themeMode, ThemeMode.system);
  });
}
