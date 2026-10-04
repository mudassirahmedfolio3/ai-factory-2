import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for HealthApi
void main() {
  final instance = ApiClient().getHealthApi();

  group(HealthApi, () {
    // Health check
    //
    // Returns 200 when the API is up and the database is reachable, otherwise 503.
    //
    //Future<HealthStatus> getHealth() async
    test('test getHealth', () async {
      // TODO
    });

  });
}
