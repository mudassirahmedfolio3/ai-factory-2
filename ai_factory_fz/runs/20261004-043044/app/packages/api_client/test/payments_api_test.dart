import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for PaymentsApi
void main() {
  final instance = ApiClient().getPaymentsApi();

  group(PaymentsApi, () {
    // Confirm mock payment
    //
    // No card PAN/CVV fields accepted.
    //
    //Future<MockPaymentConfirmResponse> confirmMockPayment(MockPaymentConfirmRequest mockPaymentConfirmRequest) async
    test('test confirmMockPayment', () async {
      // TODO
    });

  });
}
