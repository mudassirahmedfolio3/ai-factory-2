import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for OrdersApi
void main() {
  final instance = ApiClient().getOrdersApi();

  group(OrdersApi, () {
    // Order detail
    //
    //Future<OrderDetail> getOrderById(String orderId) async
    test('test getOrderById', () async {
      // TODO
    });

    // Order history
    //
    //Future<OrderListResponse> listOrders({ int page, int pageSize }) async
    test('test listOrders', () async {
      // TODO
    });

  });
}
