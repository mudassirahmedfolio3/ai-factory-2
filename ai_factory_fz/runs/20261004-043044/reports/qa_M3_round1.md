# QA report: M3

Result: **failed**

NestJS M3 APIs, seed catalog (24 SKUs), OpenAPI parity (29 operations), and imagery/docs alignment are verified with 177 passing API tests. The Flutter app remains largely M1: in-memory cart, no auth/checkout/orders/wishlist UI, home merchandising incomplete, and new M3 regression tests fail. Milestone shopper/checkout goals are not met on mobile despite backend readiness.

## Criteria checked
- US-001 partial: API getHome covered by catalog.service.spec.ts and catalog.e2e-spec.ts; Flutter HomeScreen only shows categories+featured (home_screen_test.dart); catalog.json has homeBanners but LocalCatalogDataSource.getHome omits banners/newArrivals (local_home_merchandising_test.dart fails); API-fallback works via catalog_repository_fallback_test.dart
- US-002 met for browse path: catalog_repository_test.dart, catalog-product.filters.spec.ts (API), product_listing_screen_test.dart; asset catalog.json has 24 products (catalog_repository_test loads catalog.json)
- US-003 met in Flutter catalog screens: product_detail_screen_test.dart, product_detail_notifier_test.dart; bundled images enforced by catalog-image-manifest.spec.ts (API)
- US-004 not met on client: no lib/features/auth, no AuthApi usage, flutter_secure_storage unused; backend auth.e2e-spec.ts and cart mergeGuestCart in cart.e2e-spec.ts pass
- US-005 partial: cart_screen_test.dart and cart_notifier_test.dart for in-memory cart only; no CartApi, no stock cap on quantity (cart.dart setQuantity uncapped); backend cart.service.spec.ts enforces stock
- US-006 partial: guest prompt snackbar on account_screen_test.dart only; no wishlist screens or WishlistApi in app/lib; backend wishlist.e2e-spec.ts passes
- US-007–US-010 not met on client: no checkout/order/payment screens or routes; CartScreen shows placeholder (m3_checkout_entry_test.dart fails); backend checkout.e2e-spec.ts, payments.e2e-spec.ts pass
- US-011 not met on client: Account order history shows sign-in snackbar only; backend orders.e2e-spec.ts passes
- US-012 partial: backend auth.e2e-spec.ts forgot/reset password; no Flutter forgot-password UI
- US-013 met: support_screen_test.dart and SupportContent demo disclaimers
- US-014 met on shared data/CI: catalog.json SHA256 identical app vs apps/api; catalog-seed.loader.spec.ts M3 parity; docs/IMAGE_SOURCES.md present; openapi.controller-operation-ids.spec.ts + m3-api.operations.spec.ts; flutter analyze clean; npm test 177/177 pass; flutter test 66 pass, 2 fail after QA additions

## Bugs
### BUG-001 [blocker] Flutter auth session not implemented (no register/login/logout or secure token storage) (WI-013)
Steps: 1. Open app/lib/features — no auth feature folder. 2. grep app/lib for AuthApi, flutter_secure_storage — only pubspec dependency, no usage. 3. Account tab shows copy only; no sign-in flow.
Expected: Registered shoppers can register, log in, refresh JWT, log out; access tokens stored with flutter_secure_storage per mobile conventions.
Actual: No auth screens, providers, or API client auth calls; milestone requires registered shopping with JWT.

### BUG-002 [blocker] Cart remains session-only in-memory; server cart and guest merge not integrated (WI-014)
Steps: 1. Read app/lib/features/cart/presentation/cart_notifier.dart (comment: session-only, no API). 2. grep app/lib for CartApi — no matches. 3. Register/login flow absent so mergeGuestCart cannot run.
Expected: Guest cart uses X-Guest-Cart-Id via API; login/register merges into persisted user cart per OpenAPI.
Actual: CartNotifier keeps local Map state only; backend cart.e2e-spec.ts passes but mobile does not call it.

### BUG-003 [blocker] Checkout flow UI not implemented; cart Checkout shows MVP placeholder (WI-015)
Steps: 1. Open CartScreen, tap Checkout. 2. Or run flutter test test/features/cart/m3_checkout_entry_test.dart.
Expected: Navigate to UK checkout preview with address, shipping, coupon, and server-calculated totals.
Actual: SnackBar text 'Checkout coming in full MVP'; no /checkout routes in app_router.dart.

### BUG-004 [blocker] Mock payment and order confirmation not wired in Flutter (WI-016)
Steps: 1. Confirm no payments/checkout feature under app/lib/features. 2. Backend payments.e2e-spec.ts and checkout.e2e-spec.ts pass in isolation.
Expected: Payment step uses mock secure confirmation; order confirmation screen with order number after success.
Actual: No payment or confirmation screens; shopper cannot complete purchase in app despite API implementation.

### BUG-005 [major] Coupon entry at checkout missing in mobile app (WI-017)
Steps: 1. Search app/lib for coupon or CheckoutPreview — none. 2. checkout-coupon.service.spec.ts passes on server.
Expected: Checkout UI applies one seeded coupon with server validation and updated totals in pence.
Actual: No checkout UI; coupons only testable via API e2e.

### BUG-006 [major] Wishlist feature not implemented in Flutter (WI-018)
Steps: 1. Account > Wishlist shows SnackBar 'Sign in to use this feature' (account_screen.dart). 2. No wishlist routes or WishlistApi usage in app/lib.
Expected: Signed-in users add/remove wishlist items via API and see WishlistScreen.
Actual: Only placeholder menu tile; backend wishlist.e2e-spec.ts passes.

### BUG-007 [major] Order history and order detail screens not implemented (WI-020)
Steps: 1. Account > Order history — sign-in snackbar only. 2. No OrdersApi usage in app/lib.
Expected: Signed-in user sees paginated orders and detail with status/tracking from API.
Actual: No order history UI; backend orders.e2e-spec.ts passes.

### BUG-008 [major] Password reset demo UI missing in Flutter (WI-024)
Steps: 1. Search app/lib for forgot-password or reset-password — no screens. 2. auth.e2e-spec.ts covers API.
Expected: Forgot-password form with generic success message; reset flow reachable in demo.
Actual: API stub only; no mobile screens or routes.

### BUG-009 [major] Home merchandising incomplete: no banners/new arrivals in UI or offline getHome (WI-019)
Steps: 1. Run flutter test test/features/home/local_home_merchandising_test.dart — home.banners.length is 0. 2. Open HomeScreen — only 'Shop by room' and 'Featured' sections (home_screen.dart). 3. catalog.json lines 1663+ contain homeBanners ignored by CatalogSeedDocument/local getHome.
Expected: Home shows API-backed banners, featured, new arrivals; offline fallback includes seeded banners from catalog.json.
Actual: HomeData model supports banners/newArrivals but LocalCatalogDataSource.getHome never populates them; HomeScreen does not render banners or new arrivals even when API would supply them.

### BUG-010 [major] Cart quantity updates ignore variant stock limits (WI-014)
Steps: 1. In cart_notifier_test.dart, setQuantity(inStockVariantId, 3) succeeds without stock lookup. 2. cart.dart setQuantity has no maxStock check.
Expected: Increasing quantity beyond available stock is rejected with out-of-stock/max message (matches CartService INSUFFICIENT_STOCK).
Actual: Client allows arbitrary quantities; overselling possible before checkout.

### BUG-011 [minor] Flutter test suite not green after M3 acceptance regression tests (WI-026)
Steps: Run flutter test from app/ after adding M3 tests.
Expected: All flutter test pass for M3 QA sign-off.
Actual: 66 tests run, 2 failed: local_home_merchandising_test.dart, m3_checkout_entry_test.dart (64 passed before additions).
