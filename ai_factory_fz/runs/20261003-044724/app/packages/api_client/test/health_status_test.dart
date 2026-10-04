import 'package:api_client/api_client.dart';
import 'package:test/test.dart';

void main() {
  test('HealthResponse builder exposes required fields', () {
    final instance = HealthResponse(
      (b) => b
        ..status = HealthResponseStatusEnum.ok
        ..database = HealthResponseDatabaseEnum.up
        ..timestamp = DateTime.utc(2026, 1, 1),
    );

    expect(instance.status, HealthResponseStatusEnum.ok);
    expect(instance.database, HealthResponseDatabaseEnum.up);
  });
}
