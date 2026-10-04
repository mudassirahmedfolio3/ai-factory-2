# QA report: M3

Result: **failed**

Ran server unit tests (116 passed), server e2e (16 passed, 25 DB-backed cases skipped locally without Postgres), flutter analyze (clean), and flutter test (64 passed). OpenAPI parity checks (byte-identical docs/server copies, 24 M3 operationIds, controller operationId spec) pass. Fixed stale health e2e assertions (database: reachable → up + timestamp) so CI Postgres runs align with docs/openapi.yaml. Two major seed-data gaps block US-004 and US-005 when USE_API_CATALOG=true for the Android API demo.

## Criteria checked
- US-001 register/login/logout: server/test/auth-account.e2e-spec.ts + server/src/auth/auth.service.spec.ts (bcrypt hash, tokens); app/test/features/auth/presentation/auth_screen_test.dart; app/test/core/storage/token_storage_test.dart (secure storage write/clear); AuthRepository.logout clears TokenStorage
- US-001 legal placeholders: auth_screen_test.dart + account_screen_test.dart assert Privacy Policy and Terms of Sale links
- US-002 mock password reset: auth-account.e2e-spec.ts full forgot/reset/login path; app/test/features/auth/presentation/password_reset_screen_test.dart (email step only)
- US-003 guest cart: cart_controller_test.dart + cart_screen_test.dart (cents, OOS); server/src/cart/cart.service.spec.ts merge/guest_wins; m3-shopper-flow.e2e-spec.ts cart/merge (skipped without DB); CartMergeService + AuthNotifier login merge wiring in lib
- US-004 merchandised home: home_screen_test.dart (sections with fake data); server/home.service.spec.ts; m3-api-contract GET /home (DB e2e) — seeded categories do NOT match PRD names (see BUG-001)
- US-005 search/sort/filter: catalog_filters_test.dart + product_list_screen_test.dart; server/catalog.service.spec.ts + list-products.query.spec.ts; m2-catalog-contract.e2e-spec.ts — API seed has only 12 products / ~17 variant SKUs vs 50–100 (BUG-002)
- US-006 wishlist: wishlist_screen_test.dart + wishlist_notifier_test.dart (storage key); m3-shopper-flow wishlist import e2e (DB); wishlist_import_dialog on auth_screen.dart
- US-007 checkout shipping/tax: checkout-pricing.service.spec.ts (599 below 7500, free above, 8% tax); checkout_screen_test.dart
- US-008 single coupon: checkout-pricing.service.spec.ts + coupon_messages_test.dart + checkout_notifier_test.dart stacking block
- US-009 mock payment: m3-shopper-flow.e2e-spec.ts + orders.service.spec.ts; mock_payment_screen_test.dart + order_confirmation_screen_test.dart
- US-010 order history: orders_auth_redirect_test.dart; orders_screen_test.dart; m3-shopper-flow listOrders 401/seeded history
- US-011 tracking/status: order_status_display_test.dart + orders_screen_test.dart; m3-shopper-flow shipped order carrier/tracking
- US-012 support/legal: account_screen_test.dart support form success; m3-shopper-flow POST /support/messages
- OpenAPI contract: openapi-contract-parity.spec.ts, openapi-controller-operation-ids.spec.ts, m3-openapi-surface.e2e-spec.ts, mobile-api-operations.spec.ts
- Security review: cart/orders/wishlist/users use JwtAuthGuard; no committed secrets (JWT only in e2e defaults); forgot-password returns demoResetToken by design for demo

## Bugs
### BUG-001 [major] Seeded home categories do not match PRD launch category names (WI-010)
Steps: 1) Start API with seeded DB (docker-compose or CI Postgres). 2) GET /api/v1/home or /api/v1/categories. 3) Compare category names to US-004.
Expected: Category entry points include Clothing, Electronics, Home & Kitchen, Beauty, and Sports & Outdoors.
Actual: server/prisma/seed.ts defines only Everyday Essentials, Home & Lifestyle, Personal Care, and Gift-Friendly Bestsellers; GET /home categories reflect those four M1 slugs, not the US-004 set.

### BUG-002 [major] API catalog seed far below 50–100 SKU acceptance target (WI-010)
Steps: 1) Migrate and seed Postgres. 2) GET /api/v1/products?page=1&pageSize=100. 3) Inspect total and variant count in seed.
Expected: Roughly 50–100 seeded SKUs for search/filter demo per US-005.
Actual: PRODUCTS array in server/prisma/seed.ts has 12 products and about 17 variant SKUs (grep sku: in seed.ts); listProducts total is 12, not 50+.

### BUG-003 [minor] Home screen widget test asserts PRD categories that API seed never provides (WI-016)
Steps: 1) Read app/test/features/home/presentation/home_screen_test.dart _FakeHomeRepository categories (Clothing, Electronics). 2) Run demo with USE_API_CATALOG=true against seeded API.
Expected: Widget/regression tests should assert the same category labels shoppers see from GET /home.
Actual: Test passes with fake Clothing/Electronics while API-backed home shows Personal Care / Gift-Friendly etc., masking BUG-001 in CI.

### BUG-004 [minor] No automated test covers full in-app password reset success path on mobile (WI-015)
Steps: 1) Review app/test/features/auth/presentation/password_reset_screen_test.dart. 2) Attempt to find widget test for email → token → new password → login.
Expected: Widget or integration test proves mock reset flow end-to-end on SCR-02.
Actual: Only email-step UI test exists; backend auth-account.e2e-spec.ts covers API reset but mobile submit/confirm steps are untested.
