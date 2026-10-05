import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/router/app_routes.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/account/presentation/account_screen.dart';
import 'package:shopease_app/features/support/presentation/support_screen.dart';

void main() {
  testWidgets('AccountScreen navigates to customer support', (
    WidgetTester tester,
  ) async {
    final router = GoRouter(
      initialLocation: AppRoutes.account,
      routes: [
        GoRoute(
          path: AppRoutes.account,
          builder: (context, state) => const AccountScreen(),
        ),
        GoRoute(
          path: AppRoutes.support,
          builder: (context, state) => const SupportScreen(),
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp.router(theme: AppTheme.light(), routerConfig: router),
    );

    expect(find.text('Customer support'), findsOneWidget);

    await tester.tap(find.text('Customer support'));
    await tester.pumpAndSettle();

    expect(find.text('Customer support'), findsWidgets);
    expect(find.text('0800 047 5863'), findsOneWidget);
  });
}
