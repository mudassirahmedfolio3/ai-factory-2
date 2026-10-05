import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shopease_app/core/router/app_routes.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/support/data/support_content.dart';
import 'package:shopease_app/features/support/presentation/support_faq_screen.dart';
import 'package:shopease_app/features/support/presentation/support_screen.dart';

void main() {
  testWidgets('SupportScreen shows UK contact details and policy copy', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(theme: AppTheme.light(), home: const SupportScreen()),
    );
    await tester.pumpAndSettle();

    expect(find.text(SupportContent.businessHoursTitle), findsOneWidget);
    expect(find.text(SupportContent.businessHoursBody), findsOneWidget);
    expect(find.text(SupportContent.phoneDisplay), findsOneWidget);
    expect(find.text(SupportContent.emailAddress), findsOneWidget);
    expect(find.text(SupportContent.returnsSectionTitle), findsOneWidget);
    expect(find.textContaining('handled by our support team'), findsOneWidget);
    expect(find.text(SupportContent.demoDisclaimerTitle), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text(SupportContent.openFaqButtonLabel),
      100,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text(SupportContent.openFaqButtonLabel), findsOneWidget);
  });

  testWidgets('SupportScreen opens FAQ screen', (WidgetTester tester) async {
    final router = GoRouter(
      initialLocation: AppRoutes.support,
      routes: [
        GoRoute(
          path: AppRoutes.support,
          builder: (context, state) => const SupportScreen(),
          routes: [
            GoRoute(
              path: 'faq',
              builder: (context, state) => const SupportFaqScreen(
                contentOverride: Text('FAQ test content'),
              ),
            ),
          ],
        ),
      ],
    );

    await tester.pumpWidget(
      MaterialApp.router(theme: AppTheme.light(), routerConfig: router),
    );

    await tester.scrollUntilVisible(
      find.text(SupportContent.openFaqButtonLabel),
      100,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.tap(find.text(SupportContent.openFaqButtonLabel));
    await tester.pumpAndSettle();

    expect(find.text('FAQ test content'), findsOneWidget);
    expect(find.text(SupportContent.faqScreenTitle), findsOneWidget);
  });
}
