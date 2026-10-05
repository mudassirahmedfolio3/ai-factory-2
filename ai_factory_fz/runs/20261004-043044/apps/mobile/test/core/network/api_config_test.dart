import 'package:flutter_test/flutter_test.dart';
import 'package:lighting_retail_mobile/core/network/api_config.dart';

void main() {
  test('debug default baseUrl targets Android emulator host', () {
    expect(
      ApiConfig.debugEmulatorBaseUrl,
      'http://10.0.2.2:3000/api/v1',
    );
  });

  test('baseUrl in test mode uses emulator URL when API_BASE_URL unset', () {
    expect(ApiConfig.baseUrl, ApiConfig.debugEmulatorBaseUrl);
  });

  test('release production URL is HTTPS', () {
    expect(ApiConfig.productionBaseUrl.startsWith('https://'), isTrue);
    expect(ApiConfig.stagingBaseUrl.startsWith('https://'), isTrue);
  });
}
