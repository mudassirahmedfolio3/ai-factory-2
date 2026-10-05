import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/account/presentation/account_screen.dart';
import 'package:shopease_app/features/auth/domain/auth_models.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/orders/domain/order_status_display.dart';
import 'package:shopease_app/features/support/presentation/account_support_notifier.dart';
import '../../../support/fixed_auth_notifier.dart';

void main() {
  testWidgets('guest account shows sign in and legal links', (tester) async {
    final container = ProviderContainer(
      overrides: [authNotifierProvider.overrideWith(GuestAuthNotifier.new)],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AccountScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sign in or register'), findsOneWidget);
    expect(find.text('Privacy Policy'), findsOneWidget);
    expect(find.text('Terms of Sale'), findsOneWidget);
  });

  testWidgets('signed-in account shows support email and order history link', (
    tester,
  ) async {
    final container = ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(
          () => FixedAuthNotifier(
            const AuthUser(id: 'user-1', email: 'shopper@example.com'),
          ),
        ),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AccountScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Signed in as'), findsOneWidget);
    expect(find.textContaining('shopper@example.com'), findsWidgets);
    expect(find.text(OrderStatusDisplay.supportEmail), findsOneWidget);
    expect(find.text('Order history'), findsOneWidget);
    expect(find.text('Send message'), findsOneWidget);
  });

  testWidgets('support form submit shows success message', (tester) async {
    final container = ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(
          () => FixedAuthNotifier(
            const AuthUser(id: 'user-1', email: 'shopper@example.com'),
          ),
        ),
        accountSupportNotifierProvider.overrideWith(_FakeSupportNotifier.new),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AccountScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.widgetWithText(TextFormField, 'Name'), 'Ada');
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'shopper@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Subject'),
      'Help with order',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Message'),
      'Where is my package?',
    );
    await tester.ensureVisible(find.text('Send message'));
    await tester.tap(find.text('Send message'));
    await tester.pumpAndSettle();

    expect(find.text('Message sent (simulated).'), findsOneWidget);
  });
}

class _FakeSupportNotifier extends AccountSupportNotifier {
  @override
  AccountSupportState build() => const AccountSupportState();

  @override
  Future<void> submit({
    required String name,
    required String email,
    required String subject,
    required String message,
  }) async {
    state = const AccountSupportState(
      successMessage: 'Message sent (simulated).',
    );
  }
}
