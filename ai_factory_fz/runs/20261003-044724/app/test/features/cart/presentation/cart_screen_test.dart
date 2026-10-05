import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/core/widgets/loading_skeleton.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import '../../../support/fixed_auth_notifier.dart';
import 'package:shopease_app/features/cart/presentation/cart_controller.dart';
import 'package:shopease_app/features/cart/presentation/cart_screen.dart';

void main() {
  ProviderContainer testContainer() {
    return ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestCartStorageProvider.overrideWithValue(
          InMemoryGuestCartLocalRepository(),
        ),
      ],
    );
  }

  testWidgets('shows loading then empty state for new guest session', (
    tester,
  ) async {
    final container = testContainer();
    addTearDown(container.dispose);

    await tester.pumpWidget(_buildApp(container));
    expect(find.byType(LoadingSkeleton), findsOneWidget);

    await tester.pumpAndSettle();
    expect(find.text('Your cart is empty'), findsOneWidget);
    expect(
      find.text('Add a product to start building your basket.'),
      findsOneWidget,
    );
  });

  testWidgets('renders cart lines and updates quantities immediately', (
    tester,
  ) async {
    final container = testContainer();
    addTearDown(container.dispose);
    await container.read(cartControllerProvider.future);
    final controller = container.read(cartControllerProvider.notifier);
    await controller.addProduct(
      productId: 'product-1',
      productName: 'Citrus Hand Soap',
      variantId: 'var-1',
      variantName: '300 ml',
      unitPriceCents: 799,
      currencyCode: 'USD',
    );

    await tester.pumpWidget(_buildApp(container));
    await tester.pumpAndSettle();

    expect(find.text('Citrus Hand Soap'), findsOneWidget);
    expect(find.textContaining('items subtotal'), findsOneWidget);
    expect(find.text('\$7.99'), findsOneWidget);

    await tester.tap(find.byTooltip('Increase quantity'));
    await tester.pumpAndSettle();

    expect(find.text('\$15.98'), findsOneWidget);

    await tester.tap(find.byTooltip('Decrease quantity'));
    await tester.pumpAndSettle();
    expect(find.text('\$7.99'), findsOneWidget);

    await tester.tap(find.byTooltip('Remove item'));
    await tester.pumpAndSettle();
    expect(find.text('Your cart is empty'), findsOneWidget);
  });
}

Widget _buildApp(ProviderContainer container) {
  return UncontrolledProviderScope(
    container: container,
    child: MaterialApp(theme: AppTheme.lightTheme, home: const CartScreen()),
  );
}
