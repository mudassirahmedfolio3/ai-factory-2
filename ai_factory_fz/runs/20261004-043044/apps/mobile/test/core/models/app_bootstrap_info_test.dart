import 'package:flutter_test/flutter_test.dart';
import 'package:lighting_retail_mobile/core/models/app_bootstrap_info.dart';

void main() {
  test('AppBootstrapInfo serializes to JSON', () {
    const info = AppBootstrapInfo(
      apiBaseUrl: 'http://10.0.2.2:3000/api/v1',
      usesCleartext: true,
    );
    final json = info.toJson();
    expect(json['apiBaseUrl'], info.apiBaseUrl);
    expect(json['usesCleartext'], true);
    expect(AppBootstrapInfo.fromJson(json), info);
  });
}
