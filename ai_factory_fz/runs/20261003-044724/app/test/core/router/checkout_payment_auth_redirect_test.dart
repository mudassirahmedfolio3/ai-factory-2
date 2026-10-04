import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/router/app_router.dart';
import 'package:shopease_app/features/auth/presentation/auth_screen.dart';
import 'package:shopease_app/features/checkout/presentation/mock_payment_screen.dart';

void main() {
  testWidgets('guest navigating to mock payment is redirected to auth', (
    tester,
  ) async {
    final container = ProviderContainer();
    addTearDown(container.dispose);

    final router = container.read(appRouterProvider);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp.router(routerConfig: router),
      ),
    );

    router.go(MockPaymentScreen.routePath);
    await tester.pumpAndSettle();

    expect(router.state.uri.path, AuthScreen.routePath);
    expect(
      router.state.uri.queryParameters['redirect'],
      MockPaymentScreen.routePath,
    );
  });
}
