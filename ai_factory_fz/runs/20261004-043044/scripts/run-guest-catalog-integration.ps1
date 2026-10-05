# Guest catalog journey on Android emulator (API 26+) with local catalog fallback.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $Root "app")

flutter pub get
dart run build_runner build --delete-conflicting-outputs

$deviceArgs = @()
if ($env:FLUTTER_DEVICE) {
  $deviceArgs = @("-d", $env:FLUTTER_DEVICE)
}

flutter test integration_test/guest_catalog_flow_test.dart @deviceArgs
