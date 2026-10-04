import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test(
    'debug network security config permits cleartext only for 10.0.2.2',
    () {
      final config = File(
        'android/app/src/debug/res/xml/network_security_config.xml',
      ).readAsStringSync();

      expect(config, contains('cleartextTrafficPermitted="true"'));
      expect(config, contains('10.0.2.2'));
      expect(config, isNot(contains('cleartextTrafficPermitted="true"/>')));
      // Domain whitelist should not open all hosts.
      expect(config.toLowerCase(), isNot(contains('<base-config')));
    },
  );

  test(
    'debug AndroidManifest does not enable global cleartext traffic',
    () {
      final manifest = File(
        'android/app/src/debug/AndroidManifest.xml',
      ).readAsStringSync();

      expect(manifest, contains('android:networkSecurityConfig'));
      expect(
        manifest,
        isNot(contains('android:usesCleartextTraffic="true"')),
        reason:
            'Cleartext must be limited to 10.0.2.2 via networkSecurityConfig only.',
      );
    },
  );

  test('release main manifest stays cleartext-safe', () {
    final manifest = File(
      'android/app/src/main/AndroidManifest.xml',
    ).readAsStringSync();

    expect(manifest, isNot(contains('usesCleartextTraffic="true"')));
  });
}
