import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/checkout/domain/coupon_messages.dart';
import 'package:shopease_app/features/checkout/presentation/checkout_notifier.dart';

void main() {
  test('applyCoupon blocks stacking when a different code is entered', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final notifier = container.read(checkoutNotifierProvider.notifier);
    notifier
      ..state = container.read(checkoutNotifierProvider).copyWith(
        appliedCouponCode: 'SAVE10',
      )
      ..updateCouponInput('OTHER');
    notifier.applyCoupon();
    expect(
      container.read(checkoutNotifierProvider).couponFieldError,
      CouponMessages.stackingBlocked,
    );
  });
}
