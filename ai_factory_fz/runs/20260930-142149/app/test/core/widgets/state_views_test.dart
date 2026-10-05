import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/widgets/state_views.dart';

Widget _wrap(Widget child) => MaterialApp(
  theme: AppTheme.light,
  home: Scaffold(body: child),
);

void main() {
  testWidgets('LoadingView shows a labelled progress indicator', (
    tester,
  ) async {
    final handle = tester.ensureSemantics();
    await tester.pumpWidget(_wrap(const LoadingView()));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.bySemanticsLabel('Loading'), findsOneWidget);
    handle.dispose();
  });

  testWidgets('EmptyState shows message and optional 48dp action', (
    tester,
  ) async {
    var tapped = false;
    await tester.pumpWidget(
      _wrap(
        EmptyState(
          message: 'Your cart is empty',
          actionLabel: 'Browse products',
          onAction: () => tapped = true,
        ),
      ),
    );
    expect(find.text('Your cart is empty'), findsOneWidget);
    final button = find.widgetWithText(FilledButton, 'Browse products');
    expect(button, findsOneWidget);
    final size = tester.getSize(button);
    expect(size.height, greaterThanOrEqualTo(AppSizes.minTouchTarget));

    await tester.tap(button);
    expect(tapped, isTrue);
  });

  testWidgets('EmptyState without action shows no button', (tester) async {
    await tester.pumpWidget(
      _wrap(const EmptyState(message: 'No products available')),
    );
    expect(find.text('No products available'), findsOneWidget);
    expect(find.byType(FilledButton), findsNothing);
  });

  testWidgets('ErrorState offers Retry that calls back', (tester) async {
    var retries = 0;
    await tester.pumpWidget(
      _wrap(ErrorState(message: 'Could not load', onRetry: () => retries++)),
    );
    expect(find.text('Could not load'), findsOneWidget);
    await tester.tap(find.text('Retry'));
    expect(retries, 1);
    expect(
      tester.getSize(find.byType(FilledButton)).height,
      greaterThanOrEqualTo(AppSizes.minTouchTarget),
    );
  });
}
