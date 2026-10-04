import 'package:api_client/api_client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/checkout/domain/checkout_address_draft.dart';
import 'package:shopease_app/features/checkout/domain/checkout_models.dart';
import 'package:shopease_app/features/checkout/presentation/checkout_notifier.dart';
import 'package:shopease_app/features/checkout/presentation/mock_payment_notifier.dart';
import 'package:shopease_app/features/checkout/presentation/mock_payment_screen.dart';

class _FakeMockPaymentNotifier extends MockPaymentNotifier {
  _FakeMockPaymentNotifier(this.initial);

  final MockPaymentState initial;

  @override
  MockPaymentState build() => initial;

  @override
  Future<void> initializeFromDraft(CheckoutDraft draft) async {}
}

void main() {
  testWidgets('mock payment screen shows demo pay now card when order ready', (
    tester,
  ) async {
    final order = OrderDetail(
      (b) => b
        ..id = '44444444-4444-4444-8444-444444444444'
        ..orderNumber = 'SE-DEMO-1001'
        ..createdAt = DateTime.utc(2026, 1, 1)
        ..shopperStatus = ShopperOrderStatus.awaitingPayment
        ..backendStatus = OrderDetailBackendStatusEnum.pendingPayment
        ..subtotal.replace(Money((m) => m
          ..amountCents = 799
          ..currency = 'USD'))
        ..discount.replace(Money((m) => m
          ..amountCents = 0
          ..currency = 'USD'))
        ..shipping.replace(Money((m) => m
          ..amountCents = 599
          ..currency = 'USD'))
        ..tax.replace(Money((m) => m
          ..amountCents = 64
          ..currency = 'USD'))
        ..total.replace(Money((m) => m
          ..amountCents = 1462
          ..currency = 'USD'))
        ..shippingAddress.replace(
          ShippingAddress(
            (a) => a
              ..fullName = 'Ada Lovelace'
              ..line1 = '123 Main'
              ..city = 'Austin'
              ..region = 'TX'
              ..postalCode = '78701'
              ..country = ShippingAddressCountryEnum.US,
          ),
        )
        ..lines = ListBuilder<OrderLineItem>(),
    );

    final draft = CheckoutDraft(
      address: const CheckoutAddressDraft(
        fullName: 'Ada Lovelace',
        line1: '123 Main',
        city: 'Austin',
        region: 'TX',
        postalCode: '78701',
      ),
      quote: CheckoutQuoteView(
        lines: const [],
        subtotalCents: 799,
        discountCents: 0,
        shippingCents: 599,
        taxCents: 64,
        totalCents: 1462,
        currencyCode: 'USD',
        coupon: CouponValidation((c) => c..valid = true),
      ),
      appliedCouponCode: null,
      useServerCart: false,
      guestLines: const [],
      idempotencyKey: 'test-key',
    );

    final container = ProviderContainer(
      overrides: [
        checkoutDraftProvider.overrideWith(() => _DraftHolder(draft)),
        mockPaymentNotifierProvider.overrideWith(
          () => _FakeMockPaymentNotifier(
            MockPaymentState(phase: MockPaymentPhase.ready, order: order),
          ),
        ),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const MockPaymentScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Pay now'), findsOneWidget);
    expect(find.textContaining('SE-DEMO-1001'), findsOneWidget);
    expect(find.text('Cancel payment'), findsOneWidget);
  });
}

class _DraftHolder extends CheckoutDraftHolder {
  _DraftHolder(this._draft);

  final CheckoutDraft _draft;

  @override
  CheckoutDraft? build() => _draft;
}
