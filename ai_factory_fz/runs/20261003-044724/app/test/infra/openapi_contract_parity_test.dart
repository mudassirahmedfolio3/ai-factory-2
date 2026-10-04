import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

/// Pins app/openapi.yaml (Dart client generator input) to docs/openapi.yaml.
void main() {
  test('app/openapi.yaml stays byte-identical to docs/openapi.yaml', () {
    // flutter test runs with cwd = app/
    final docsCopy = File('../docs/openapi.yaml');
    final appCopy = File('openapi.yaml');

    expect(docsCopy.readAsBytesSync(), appCopy.readAsBytesSync());
  });
}
