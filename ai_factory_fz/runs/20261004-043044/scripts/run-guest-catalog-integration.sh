#!/usr/bin/env bash
# Guest catalog journey on Android emulator or attached device (M2 demo path).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/app"

DEVICE="${FLUTTER_DEVICE:-}"
DEVICE_ARGS=()
if [[ -n "$DEVICE" ]]; then
  DEVICE_ARGS=(-d "$DEVICE")
fi

flutter pub get
dart run build_runner build --delete-conflicting-outputs

# In-memory M1 catalog overrides (API intentionally not required).
flutter test integration_test/guest_catalog_flow_test.dart \
  "${DEVICE_ARGS[@]}"
