import 'package:api_client/api_client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/auth/presentation/auth_notifier.dart';
import 'package:shopease_app/features/cart/data/guest_cart_storage.dart';
import 'package:shopease_app/features/checkout/presentation/order_confirmation_screen.dart';
import '../../../support/fixed_auth_notifier.dart';

void main() {
  testWidgets('confirmation screen shows order number and total', (tester) async {
    final order = OrderDetail(
      (b) => b
        ..id = '44444444-4444-4444-8444-444444444444'
        ..orderNumber = 'SE-DEMO-2042'
        ..createdAt = DateTime.utc(2026, 1, 2)
        ..shopperStatus = ShopperOrderStatus.processing
        ..backendStatus = OrderDetailBackendStatusEnum.paid
        ..subtotal.replace(Money((m) => m
          ..amountCents = 799
          ..currency = 'USD'))
        ..discount.replace(Money((m) => m
          ..amountCents = 0
          ..currency = 'USD'))
        ..shipping.replace(Money((m) => m
          ..amountCents = 0
          ..currency = 'USD'))
        ..tax.replace(Money((m) => m
          ..amountCents = 64
          ..currency = 'USD'))
        ..total.replace(Money((m) => m
          ..amountCents = 863
          ..currency = 'USD'))
        ..shippingAddress.replace(
          ShippingAddress(
            (a) => a
              ..fullName = 'Ada Lovelace'
              ..email = 'ada@example.com'
              ..line1 = '123 Main'
              ..city = 'Austin'
              ..region = 'TX'
              ..postalCode = '78701'
              ..country = ShippingAddressCountryEnum.US,
          ),
        )
        ..lines = ListBuilder<OrderLineItem>(),
    );

    final container = ProviderContainer(
      overrides: [
        authNotifierProvider.overrideWith(GuestAuthNotifier.new),
        guestCartStorageProvider.overrideWithValue(
          InMemoryGuestCartLocalRepository(),
        ),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: OrderConfirmationScreen(
            orderId: order.id,
            initialOrder: order,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Thank you!'), findsOneWidget);
    expect(find.textContaining('SE-DEMO-2042'), findsOneWidget);
    expect(find.text('\$8.63'), findsOneWidget);
    expect(find.text('Continue shopping'), findsOneWidget);
  });
}
