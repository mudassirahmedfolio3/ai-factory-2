#!/usr/bin/env bash
# Launch ShopEase on Android emulator against local/staging API (10.0.2.2:3000).
# Starts docker-compose when --up is passed; prints the M3 manual QA checklist.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="${ROOT}/app"
COMPOSE_UP=false
DEVICE="${ANDROID_DEVICE:-}"

usage() {
  echo "Usage: $0 [--up] [--device <adb-serial>]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --up) COMPOSE_UP=true; shift ;;
    --device) DEVICE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$COMPOSE_UP" == true ]]; then
  cd "${ROOT}"
  docker compose up -d --build --wait
  node "${ROOT}/scripts/run-gethealth-smoke.mjs"
fi

cat <<'CHECKLIST'

=== ShopEase M3 emulator demo (manual QA) ===
Prerequisites: Android emulator running; API reachable at http://10.0.2.2:3000 (host port 3000).
Seeded demo account: demo@shopease.test / DemoPass123!
Coupons: WELCOME10 (10% off), SAVE500 ($5 off min subtotal), GIFTEXCL15 (category exclusion demo).

1. Guest browse (SCR-03→SCR-05): Home banners/featured/categories; open product detail; add to cart.
2. Guest cart (SCR-06): Adjust qty; verify USD cents formatting; OOS variant blocked on detail.
3. Guest checkout (SCR-08→SCR-09→SCR-10): US address, review shipping/tax; invalid coupon shows error;
   valid WELCOME10 recalculates; mock Pay now → confirmation with order number.
4. Register/login (SCR-01): New user or demo login; secure session; legal links open placeholders.
5. Cart merge (SCR-06): As guest add SKU, login as demo — merged cart persists via API.
6. Wishlist (SCR-07): Guest local wishlist; signed-in API wishlist; optional import on login.
7. Orders (SCR-11/SCR-12): Order history (guest redirected to auth); seeded shipped/delivered tracking.
8. Password reset stub (SCR-02): Forgot password → mock token flow → login with new password.
9. Support (SCR-11): support@shopease-demo.com form → simulated send success.
10. Search/filters (SCR-04): Keyword, sort, price/category/brand/availability filters.

CHECKLIST

cd "${APP_DIR}"
FLUTTER_ARGS=(
  run
  --dart-define=USE_API_CATALOG=true
)
if [[ -n "${DEVICE}" ]]; then
  FLUTTER_ARGS+=(-d "${DEVICE}")
fi

echo "Running: flutter ${FLUTTER_ARGS[*]}"
exec flutter "${FLUTTER_ARGS[@]}"
