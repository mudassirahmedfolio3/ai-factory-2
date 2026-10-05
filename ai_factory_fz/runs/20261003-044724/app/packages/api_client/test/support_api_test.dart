import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for SupportApi
void main() {
  final instance = ApiClient().getSupportApi();

  group(SupportApi, () {
    // Submit support form (simulated send)
    //
    //Future<SupportMessageResponse> submitSupportMessage(SupportMessageRequest supportMessageRequest) async
    test('test submitSupportMessage', () async {
      // TODO
    });

  });
}
