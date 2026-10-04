import 'package:api_client/api_client.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import 'package:shopease_app/features/cart/presentation/cart_controller.dart';
import 'package:shopease_app/features/checkout/domain/checkout_address_draft.dart';
import 'package:shopease_app/features/checkout/domain/checkout_models.dart';
import 'package:shopease_app/features/checkout/presentation/checkout_notifier.dart';
import 'package:shopease_app/features/checkout/domain/checkout_messages.dart';
import 'package:shopease_app/features/checkout/presentation/checkout_screen.dart';
import '../../../support/fixed_auth_notifier.dart';

class _ReviewCheckoutNotifier extends CheckoutNotifier {
  @override
  CheckoutUiState build() {
    return CheckoutUiState(
      step: CheckoutUiStep.review,
      address: const CheckoutAddressDraft(
        fullName: 'Ada Lovelace',
        line1: '123 Main',
        city: 'Austin',
        region: 'TX',
        postalCode: '78701',
      ),
      quote: CheckoutQuoteView(
        lines: const [
          CheckoutQuoteLine(
            productName: 'Citrus Hand Soap',
            variantName: '300 ml',
            quantity: 1,
            unitPriceCents: 799,
            lineTotalCents: 799,
            currencyCode: 'USD',
          ),
        ],
        subtotalCents: 799,
        discountCents: 0,
        shippingCents: 599,
        taxCents: 64,
        totalCents: 1462,
        currencyCode: 'USD',
        coupon: CouponValidation((b) => b..valid = true),
        taxDisclaimer: 'Final tax may vary.',
      ),
    );
  }
}

void main() {
  ProviderContainer testContainer() {
    return ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestCartStorageProvider.overrideWithValue(
          InMemoryGuestCartLocalRepository(),
        ),
        checkoutNotifierProvider.overrideWith(_ReviewCheckoutNotifier.new),
      ],
    );
  }

  testWidgets('checkout review shows shipping tax and total from quote', (
    tester,
  ) async {
    final container = testContainer();
    addTearDown(container.dispose);
    await container.read(cartControllerProvider.future);
    await container.read(cartControllerProvider.notifier).addProduct(
      productId: '33333333-3333-4333-8333-333333333333',
      productName: 'Citrus Hand Soap',
      variantId: '22222222-2222-4222-8222-222222222222',
      variantName: '300 ml',
      unitPriceCents: 799,
      currencyCode: 'USD',
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const CheckoutScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Citrus Hand Soap'), findsOneWidget);
    expect(find.text('Shipping'), findsWidgets);
    expect(find.text('Estimated tax'), findsOneWidget);
    expect(find.text('Order total'), findsOneWidget);
    expect(find.text('Final tax may vary.'), findsOneWidget);
    expect(find.text('Sign in to pay'), findsOneWidget);
    expect(find.textContaining(CheckoutMessages.signInBeforePayment), findsOneWidget);
  });
}
