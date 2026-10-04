import 'package:api_client/api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/checkout/domain/coupon_messages.dart';

void main() {
  test('maps coupon rejection reasons to shopper copy', () {
    expect(
      CouponMessages.rejectionMessage(
        CouponValidation((b) => b..valid = false
          ..rejectionReason = CouponValidationRejectionReasonEnum.expired),
      ),
      'This coupon has expired.',
    );
    expect(
      CouponMessages.rejectionMessage(
        CouponValidation((b) => b..valid = false
          ..rejectionReason =
              CouponValidationRejectionReasonEnum.alreadyApplied),
      ),
      'Only one coupon code is allowed per order.',
    );
  });
}
