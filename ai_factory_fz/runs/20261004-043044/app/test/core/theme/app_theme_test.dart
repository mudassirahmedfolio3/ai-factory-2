import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_color_tokens.dart';
import 'package:shopease_app/core/theme/app_spacing.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/theme/app_typography.dart';

void main() {
  test('light theme uses design-system primary colour', () {
    final theme = AppTheme.light();
    expect(theme.colorScheme.primary, AppColorTokens.lightPrimary);
    expect(theme.colorScheme.surface, AppColorTokens.lightSurface);
  });

  test('theme exposes custom price text styles', () {
    final theme = AppTheme.light();
    final styles = theme.extension<AppTextStyles>();
    expect(styles, isNotNull);
    expect(styles!.priceLarge.fontSize, 24);
    expect(styles.priceMedium.fontWeight, FontWeight.w700);
  });

  test('spacing touch target is at least 48dp', () {
    expect(AppSpacing.touchTarget, greaterThanOrEqualTo(48));
  });
}
