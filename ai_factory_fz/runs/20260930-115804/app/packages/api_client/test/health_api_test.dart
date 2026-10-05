import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for HealthApi
void main() {
  final instance = ApiClient().getHealthApi();

  group(HealthApi, () {
    // Health check
    //
    // Returns 200 when the service and its database are reachable, 503 otherwise. Public endpoint.
    //
    //Future<HealthStatus> getHealth() async
    test('test getHealth', () async {
      // TODO
    });

  });
}
