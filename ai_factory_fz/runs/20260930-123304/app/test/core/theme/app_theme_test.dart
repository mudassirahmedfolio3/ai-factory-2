import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/theme/tokens.dart';

void main() {
  test('light theme is built from the light tokens', () {
    final theme = AppTheme.light;
    expect(theme.useMaterial3, isTrue);
    expect(theme.colorScheme.brightness, Brightness.light);
    expect(theme.colorScheme.primary, AppColorTokens.light.primary);
    expect(theme.colorScheme.error, AppColorTokens.light.error);
    expect(theme.scaffoldBackgroundColor, AppColorTokens.light.background);
    expect(theme.extension<AppTokens>(), AppTokens.light);
    expect(theme.textTheme.titleMedium?.fontSize, 16);
    expect(theme.textTheme.headlineMedium?.fontWeight, FontWeight.w700);
  });

  test('dark theme is built from the dark tokens', () {
    final theme = AppTheme.dark;
    expect(theme.colorScheme.brightness, Brightness.dark);
    expect(theme.colorScheme.primary, AppColorTokens.dark.primary);
    expect(theme.extension<AppTokens>(), AppTokens.dark);
  });

  test('spacing scale and touch target match the design system', () {
    expect(AppSpacing.scale, [4, 8, 12, 16, 24, 32, 48]);
    expect(AppSizes.minTouchTarget, 48);
    expect(AppRadii.pill, 999);
  });

  testWidgets('filled buttons meet the 48dp minimum touch target', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light,
        home: Scaffold(
          body: Center(
            child: FilledButton(onPressed: () {}, child: const Text('Go')),
          ),
        ),
      ),
    );
    final size = tester.getSize(find.byType(FilledButton));
    expect(size.height, greaterThanOrEqualTo(AppSizes.minTouchTarget));
    expect(size.width, greaterThanOrEqualTo(AppSizes.minTouchTarget));
  });
}
