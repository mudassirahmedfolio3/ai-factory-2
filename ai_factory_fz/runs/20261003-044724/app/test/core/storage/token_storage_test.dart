import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shopease_app/core/storage/token_storage.dart';

class _MapSecureStorage extends FlutterSecureStorage {
  _MapSecureStorage() : super();

  final Map<String, String> _values = {};

  @override
  Future<void> delete({
    required String key,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    _values.remove(key);
  }

  @override
  Future<String?> read({
    required String key,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    return _values[key];
  }

  @override
  Future<void> write({
    required String key,
    required String? value,
    AppleOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    AppleOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (value == null) {
      _values.remove(key);
    } else {
      _values[key] = value;
    }
  }
}

void main() {
  test('TokenStorage writes, reads, and clears access and refresh tokens', () async {
    final storage = TokenStorage(_MapSecureStorage());

    await storage.writeTokens(
      accessToken: 'access-abc',
      refreshToken: 'refresh-xyz',
    );

    expect(await storage.readAccessToken(), 'access-abc');
    expect(await storage.readRefreshToken(), 'refresh-xyz');

    await storage.clearAll();

    expect(await storage.readAccessToken(), isNull);
    expect(await storage.readRefreshToken(), isNull);
  });
}
