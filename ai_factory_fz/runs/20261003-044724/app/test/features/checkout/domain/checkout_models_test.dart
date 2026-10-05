import 'package:api_client/api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/checkout/domain/checkout_address_draft.dart';
import 'package:shopease_app/features/checkout/domain/checkout_models.dart';

void main() {
  test('CheckoutDraft.forSession uses server cart when signed in', () {
    final draft = CheckoutDraft(
      address: const CheckoutAddressDraft(fullName: 'Ada Lovelace'),
      quote: CheckoutQuoteView(
        lines: const [],
        subtotalCents: 100,
        discountCents: 0,
        shippingCents: 599,
        taxCents: 8,
        totalCents: 707,
        currencyCode: 'USD',
        coupon: CouponValidation((b) => b..valid = true),
      ),
      appliedCouponCode: 'SAVE10',
      useServerCart: false,
      guestLines: [
        CartLineInput(
          (b) => b
            ..variantId = '22222222-2222-4222-8222-222222222222'
            ..quantity = 1,
        ),
      ],
      idempotencyKey: 'key-1',
    );

    final signedInDraft = draft.forSession(signedIn: true);
    expect(signedInDraft.useServerCart, isTrue);
    expect(signedInDraft.guestLines, isEmpty);
    expect(signedInDraft.appliedCouponCode, 'SAVE10');

    final guestDraft = draft.forSession(signedIn: false);
    expect(guestDraft.useServerCart, isFalse);
    expect(guestDraft.guestLines, hasLength(1));
  });
}
