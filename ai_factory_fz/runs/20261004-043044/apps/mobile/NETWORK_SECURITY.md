# Android network security policy

## Debug builds

- Cleartext HTTP is **only** allowed to the Android emulator host alias `10.0.2.2` (maps to the developer machine’s loopback).
- Configuration: `android/app/src/debug/res/xml/network_security_config.xml`, referenced from `android/app/src/debug/AndroidManifest.xml`.
- Default API base URL: `http://10.0.2.2:3000/api/v1` via `lib/core/network/api_config.dart`.

## Release builds

- **HTTPS only.** Release manifests do **not** include a cleartext `networkSecurityConfig`.
- The API base URL must use `https://`. Override at build time with `--dart-define=API_BASE_URL=https://...` if needed.
- Production default: `https://api.lighting-retail.example/api/v1`.
- Staging default: `https://api.staging.lighting-retail.example/api/v1`.

See also the repository root `README.md`.
