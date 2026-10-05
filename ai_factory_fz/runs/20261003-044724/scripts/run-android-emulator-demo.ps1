# Launch ShopEase on Android emulator against local/staging API (10.0.2.2:3000).
param(
  [switch]$Up,
  [string]$Device = $env:ANDROID_DEVICE
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$AppDir = Join-Path $Root 'app'

if ($Up) {
  Push-Location $Root
  try {
    docker compose up -d --build --wait
    node (Join-Path $Root 'scripts/run-gethealth-smoke.mjs')
  } finally {
    Pop-Location
  }
}

@'

=== ShopEase M3 emulator demo (manual QA) ===
Prerequisites: Android emulator running; API at http://10.0.2.2:3000 (host port 3000).
Seeded demo account: demo@shopease.test / DemoPass123!
Coupons: WELCOME10, SAVE500, GIFTEXCL15 (exclusion demo).

Guest browse→checkout→mock pay; login cart merge; coupon errors; orders/tracking;
password reset stub; support submit; search/filters — see reports/qa_M3_round1.md.

'@ | Write-Host

Push-Location $AppDir
try {
  $args = @('run', '--dart-define=USE_API_CATALOG=true')
  if ($Device) { $args += @('-d', $Device) }
  Write-Host "Running: flutter $($args -join ' ')"
  & flutter @args
} finally {
  Pop-Location
}
