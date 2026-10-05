import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

/// tests for HealthApi
void main() {
  final instance = ApiClient().getHealthApi();

  group(HealthApi, () {
    test('test getHealth', () async {
      expect(instance, isA<HealthApi>());
    });
  });
}
