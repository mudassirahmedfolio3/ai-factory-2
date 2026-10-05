import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';

void main() {
  group('AppTheme', () {
    test('light theme maps colour tokens into the ColorScheme', () {
      final theme = AppTheme.light;
      final scheme = theme.colorScheme;
      expect(scheme.brightness, Brightness.light);
      expect(scheme.primary, AppPalette.light.primary);
      expect(scheme.onPrimary, AppPalette.light.onPrimary);
      expect(scheme.error, AppPalette.light.error);
      expect(scheme.surface, AppPalette.light.surface);
      expect(theme.scaffoldBackgroundColor, AppPalette.light.background);
    });

    test('dark theme uses the dark palette', () {
      final scheme = AppTheme.dark.colorScheme;
      expect(scheme.brightness, Brightness.dark);
      expect(scheme.primary, AppPalette.dark.primary);
      expect(scheme.surface, AppPalette.dark.surface);
    });

    test('custom tokens are exposed via the theme extension', () {
      final tokens = AppTheme.light.extension<AppThemeTokens>()!;
      expect(tokens.success, AppPalette.light.success);
      expect(tokens.warning, AppPalette.light.warning);
      expect(tokens.salePrice, AppPalette.light.salePrice);
      expect(tokens.priceStrike.decoration, TextDecoration.lineThrough);
      expect(tokens.priceLarge.fontSize, 22);
      expect(tokens.priceMedium.fontWeight, FontWeight.w700);
    });

    test('text theme follows the typography tokens', () {
      final text = AppTheme.light.textTheme;
      expect(text.headlineMedium?.fontSize, 24);
      expect(text.headlineMedium?.fontWeight, FontWeight.w700);
      expect(text.titleLarge?.fontSize, 20);
      expect(text.bodyMedium?.fontSize, 14);
      expect(text.labelMedium?.fontSize, 12);
    });

    test('buttons enforce the 48dp minimum touch target', () {
      final theme = AppTheme.light;
      const min = Size(AppSizes.minTouchTarget, AppSizes.minTouchTarget);
      expect(theme.filledButtonTheme.style?.minimumSize?.resolve({}), min);
      expect(theme.iconButtonTheme.style?.minimumSize?.resolve({}), min);
      expect(AppSizes.minTouchTarget, 48);
    });

    test('spacing and radii scales match the design system', () {
      expect(AppSpacing.scale, [0, 4, 8, 12, 16, 24, 32, 48]);
      expect(AppRadii.scale, [0, 4, 8, 12, 16, 999]);
    });

    test('lerp between light and dark tokens is well defined', () {
      final light = AppTheme.light.extension<AppThemeTokens>()!;
      final dark = AppTheme.dark.extension<AppThemeTokens>()!;
      expect(light.lerp(dark, 0).success, light.success);
      expect(light.lerp(dark, 1).success, dark.success);
    });
  });
}
