import 'package:test/test.dart';
import 'package:api_client/api_client.dart';


/// tests for HealthApi
void main() {
  final instance = ApiClient().getHealthApi();

  group(HealthApi, () {
    // Health check (200 when the database is reachable)
    //
    //Future<HealthStatus> getHealth() async
    test('test getHealth', () async {
      // TODO
    });

  });
}
