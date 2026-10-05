import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_colors.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/theme/app_typography.dart';
import 'package:shopease_app/core/widgets/empty_view.dart';
import 'package:shopease_app/core/widgets/error_view.dart';
import 'package:shopease_app/core/widgets/loading_view.dart';

void main() {
  test('light and dark themes are built from tokens', () {
    final light = AppTheme.light;
    final dark = AppTheme.dark;
    expect(light.useMaterial3, isTrue);
    expect(light.colorScheme.primary, const Color(0xFF7A4F00));
    expect(dark.colorScheme.primary, const Color(0xFFFFC857));
    expect(light.extension<AppColors>()!.stockLow, const Color(0xFF8F4B00));
    expect(
      light.extension<AppPriceTextStyles>()!.priceStruck.decoration,
      TextDecoration.lineThrough,
    );
  });

  Widget host(Widget child) => MaterialApp(
    theme: AppTheme.light,
    home: Scaffold(body: child),
  );

  testWidgets('LoadingView exposes Loading label', (tester) async {
    await tester.pumpWidget(host(const LoadingView()));
    expect(find.bySemanticsLabel('Loading'), findsOneWidget);
  });

  testWidgets('ErrorView shows message and runs retry', (tester) async {
    var retried = 0;
    await tester.pumpWidget(
      host(
        ErrorView(message: 'Something went wrong', onAction: () => retried++),
      ),
    );
    expect(find.text('Something went wrong'), findsOneWidget);
    expect(find.bySemanticsLabel('Error'), findsOneWidget);
    await tester.tap(find.text('Retry'));
    expect(retried, 1);
    expect(
      tester.getSize(find.byType(FilledButton)).height,
      greaterThanOrEqualTo(48),
    );
  });

  testWidgets('EmptyView shows title and optional action', (tester) async {
    var tapped = false;
    await tester.pumpWidget(
      host(
        EmptyView(
          title: 'Your cart is empty',
          actionLabel: 'Browse products',
          onAction: () => tapped = true,
        ),
      ),
    );
    expect(find.text('Your cart is empty'), findsOneWidget);
    await tester.tap(find.text('Browse products'));
    expect(tapped, isTrue);
  });
}
