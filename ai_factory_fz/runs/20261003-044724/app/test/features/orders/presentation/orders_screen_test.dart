import 'package:api_client/api_client.dart';
import 'package:built_collection/built_collection.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/theme/app_theme.dart';
import 'package:shopease_app/features/orders/presentation/order_detail_notifier.dart';
import 'package:shopease_app/features/orders/presentation/orders_list_notifier.dart';
import 'package:shopease_app/features/orders/presentation/orders_screen.dart';

void main() {
  testWidgets('lists orders and expands to show status stepper', (tester) async {
    const orderId = '44444444-4444-4444-8444-444444444444';
    final summary = OrderSummary(
      (b) => b
        ..id = orderId
        ..orderNumber = 'SE-DEMO-1001'
        ..createdAt = DateTime.utc(2026, 2, 1)
        ..shopperStatus = ShopperOrderStatus.processing
        ..total.replace(Money((m) => m..amountCents = 2500..currency = 'USD')),
    );

    final detail = OrderDetail(
      (b) => b
        ..id = orderId
        ..orderNumber = 'SE-DEMO-1001'
        ..createdAt = DateTime.utc(2026, 2, 1)
        ..shopperStatus = ShopperOrderStatus.processing
        ..backendStatus = OrderDetailBackendStatusEnum.paid
        ..subtotal.replace(Money((m) => m..amountCents = 2500..currency = 'USD'))
        ..discount.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
        ..shipping.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
        ..tax.replace(Money((m) => m..amountCents = 0..currency = 'USD'))
        ..total.replace(Money((m) => m..amountCents = 2500..currency = 'USD'))
        ..shippingAddress.replace(
          ShippingAddress(
            (a) => a
              ..fullName = 'Demo Shopper'
              ..line1 = '100 Market St'
              ..city = 'San Francisco'
              ..region = 'CA'
              ..postalCode = '94105'
              ..country = ShippingAddressCountryEnum.US,
          ),
        )
        ..lines = ListBuilder<OrderLineItem>([
          OrderLineItem(
            (l) => l
              ..productName = 'Demo Soap'
              ..variantName = 'Standard'
              ..sku = 'SOAP-1'
              ..quantity = 2
              ..unitPrice.replace(
                Money((m) => m..amountCents = 799..currency = 'USD'),
              )
              ..lineTotal.replace(
                Money((m) => m..amountCents = 1598..currency = 'USD'),
              ),
          ),
        ]),
    );

    final container = ProviderContainer(
      overrides: [
        ordersListNotifierProvider.overrideWith(
          () => _FixedOrdersListNotifier(
            OrdersListState(
              items: [summary],
              total: 1,
              page: 1,
              pageSize: 24,
            ),
          ),
        ),
        orderDetailProvider.overrideWith((ref, id) async => detail),
      ],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const OrdersScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('SE-DEMO-1001'), findsOneWidget);
    expect(find.text('Processing'), findsOneWidget);

    await tester.tap(find.text('SE-DEMO-1001'));
    await tester.pumpAndSettle();

    expect(find.text('Demo Soap'), findsOneWidget);
    expect(find.textContaining('Demo Shopper'), findsOneWidget);
    expect(find.text('Shipped'), findsWidgets);
    expect(find.text('Delivered'), findsWidgets);
  });

  testWidgets('empty order list shows empty state', (tester) async {
    final container = ProviderContainer(
      overrides: [
        ordersListNotifierProvider.overrideWith(
          () => _FixedOrdersListNotifier(
            const OrdersListState(items: [], total: 0, page: 1, pageSize: 24),
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
          home: const OrdersScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('No orders yet'), findsOneWidget);
  });
}

class _FixedOrdersListNotifier extends OrdersListNotifier {
  _FixedOrdersListNotifier(this._initial);

  final OrdersListState _initial;

  @override
  Future<OrdersListState> build() async => _initial;
}
