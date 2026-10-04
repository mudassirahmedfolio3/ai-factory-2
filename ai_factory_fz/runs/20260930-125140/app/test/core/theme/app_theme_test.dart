import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_colors.dart';
import 'package:shopease_app/core/theme/app_dimens.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/theme/app_typography.dart';

void main() {
  test('light theme uses the light color tokens', () {
    final theme = AppTheme.light;
    expect(theme.brightness, Brightness.light);
    expect(theme.colorScheme.primary, AppColorTokens.light.primary);
    expect(theme.colorScheme.onSurface, AppColorTokens.light.onSurface);
    expect(theme.scaffoldBackgroundColor, AppColorTokens.light.background);
    expect(
      theme.extension<AppSemanticColors>()!.outOfStockContainer,
      AppColorTokens.light.outOfStockContainer,
    );
  });

  test('dark theme uses the dark color tokens', () {
    final theme = AppTheme.dark;
    expect(theme.brightness, Brightness.dark);
    expect(theme.colorScheme.primary, AppColorTokens.dark.primary);
    expect(theme.scaffoldBackgroundColor, AppColorTokens.dark.background);
    expect(
      theme.extension<AppSemanticColors>()!.badge,
      AppColorTokens.dark.badge,
    );
  });

  test('typography tokens match the design system', () {
    final text = AppTheme.light.textTheme;
    expect(text.headlineMedium!.fontSize, 28);
    expect(text.headlineMedium!.fontWeight, FontWeight.w700);
    expect(text.titleMedium!.fontSize, 16);
    expect(text.bodyMedium!.height, closeTo(20 / 14, 1e-9));
    final price = AppTheme.light.extension<AppTextStyles>()!.price;
    expect(price.fontSize, 18);
    expect(price.fontWeight, FontWeight.w700);
    expect(AppTypography.labelSmall.fontSize, 12);
  });

  test('buttons enforce the 48dp minimum touch target', () {
    final style = AppTheme.light.filledButtonTheme.style!;
    expect(
      style.minimumSize!.resolve(<WidgetState>{}),
      const Size(AppSizes.minTouchTarget, AppSizes.minTouchTarget),
    );
    expect(AppSizes.minTouchTarget, 48);
  });

  test('spacing and radii scales match the design system', () {
    expect(
      [
        AppSpacing.xs,
        AppSpacing.sm,
        AppSpacing.md,
        AppSpacing.lg,
        AppSpacing.xl,
        AppSpacing.xxl,
        AppSpacing.xxxl,
      ],
      [4, 8, 12, 16, 24, 32, 48],
    );
    expect(
      [AppRadii.xs, AppRadii.sm, AppRadii.md, AppRadii.lg, AppRadii.pill],
      [4, 8, 12, 16, 999],
    );
  });
}
