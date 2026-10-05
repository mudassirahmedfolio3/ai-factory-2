import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for OrdersApi
void main() {
  final instance = ApiClient().getOrdersApi();

  group(OrdersApi, () {
    // Cancel pending_payment order and release stock
    //
    //Future<OrderDetail> cancelOrder(String orderId) async
    test('test cancelOrder', () async {
      // TODO
    });

    // Demo pay-now (marks order paid, no Stripe)
    //
    //Future<OrderDetail> completeMockPayment(String orderId) async
    test('test completeMockPayment', () async {
      // TODO
    });

    // Place order (pending_payment, reserves stock)
    //
    //Future<OrderDetail> createOrder(CreateOrderRequest createOrderRequest) async
    test('test createOrder', () async {
      // TODO
    });

    // Get order detail
    //
    //Future<OrderDetail> getOrderById(String orderId) async
    test('test getOrderById', () async {
      // TODO
    });

    // List my orders
    //
    //Future<OrderListResponse> listOrders({ int page, int pageSize }) async
    test('test listOrders', () async {
      // TODO
    });

  });
}
