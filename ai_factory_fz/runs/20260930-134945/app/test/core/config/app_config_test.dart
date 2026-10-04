import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/config/app_config.dart';

void main() {
  test('empty API_BASE_URL means offline (no base url)', () {
    expect(AppConfig.parse('').apiBaseUrl, isNull);
    expect(AppConfig.fromEnvironment().apiBaseUrl, isNull);
  });

  test('accepts absolute http(s) urls', () {
    expect(
      AppConfig.parse('http://10.0.2.2:3000/api/v1').apiBaseUrl.toString(),
      'http://10.0.2.2:3000/api/v1',
    );
  });

  test('rejects invalid urls', () {
    expect(() => AppConfig.parse('not a url'), throwsFormatException);
    expect(() => AppConfig.parse('ftp://x.y'), throwsFormatException);
  });
}
