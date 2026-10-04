import 'package:api_client/api_client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/features/orders/domain/order_status_display.dart';

void main() {
  group('OrderStatusDisplay', () {
    test('maps shopper fulfillment statuses to stepper indices', () {
      expect(
        OrderStatusDisplay.fulfillmentStepIndex(ShopperOrderStatus.processing),
        0,
      );
      expect(
        OrderStatusDisplay.fulfillmentStepIndex(ShopperOrderStatus.shipped),
        1,
      );
      expect(
        OrderStatusDisplay.fulfillmentStepIndex(ShopperOrderStatus.delivered),
        2,
      );
      expect(
        OrderStatusDisplay.fulfillmentStepIndex(ShopperOrderStatus.cancelled),
        isNull,
      );
    });

    test('shows tracking only when shipped or delivered with fields', () {
      final processing = OrderDetail(
        (b) => b
          ..id = '1'
          ..orderNumber = 'SE-1'
          ..createdAt = DateTime.utc(2026, 1, 1)
          ..shopperStatus = ShopperOrderStatus.processing
          ..backendStatus = OrderDetailBackendStatusEnum.paid
          ..subtotal.replace(Money((m) => m..amountCents = 100..currency = 'USD'))
          ..discount.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
          ..shipping.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
          ..tax.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
          ..total.replace(Money((m) => m..amountCents = 100..currency = 'USD'))
          ..shippingAddress.replace(_minimalAddress())
          ..carrierName = 'UPS'
          ..trackingNumber = '1Z999'
          ..lines = ListBuilder<OrderLineItem>(),
      );
      expect(OrderStatusDisplay.showTrackingSection(processing), isFalse);

      final shipped = processing.rebuild(
        (b) => b..shopperStatus = ShopperOrderStatus.shipped,
      );
      expect(OrderStatusDisplay.showTrackingSection(shipped), isTrue);
    });
  });
}

ShippingAddress _minimalAddress() {
  return ShippingAddress(
    (a) => a
      ..fullName = 'Demo'
      ..line1 = '1 Main'
      ..city = 'Austin'
      ..region = 'TX'
      ..postalCode = '78701'
      ..country = ShippingAddressCountryEnum.US,
  );
}
