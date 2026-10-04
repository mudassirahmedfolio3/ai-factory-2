# QA report: M3

Result: **passed**

M3 Release 2 shopper depth was verified against US-001–US-012 via code/traceability review and automated gates: server vitest 120/120 unit tests and 16/16 runnable e2e tests passed (25 e2e cases skipped locally because Postgres/Docker was unavailable; server-ci runs full e2e with migrated seeded DB). Flutter analyze clean; flutter test 66/66 passed. OpenAPI parity is enforced by server/openapi.yaml byte-identity to docs/openapi.yaml, openapi-controller-operation-ids.spec.ts, mobile-api-operations.spec.ts, and api_client openapi_operations_contract_test.dart. No blocker or major functional defects were found; two minor infra/convention gaps are recorded below.

## Criteria checked
- US-001 register/login/logout: server auth.service.spec.ts (bcrypt passwordHash, strong password), auth-account.e2e-spec.ts (register 201, refresh, logout 204); app auth_validators_test.dart, auth_screen_test.dart (legal links), token_storage_test.dart (secure storage), auth_repository.dart logout clears tokens; auth_notifier.dart logout + guest cart reset.
- US-001 legal placeholders: legal_document_screen.dart + routes in app_router.dart; auth_screen_test.dart and account_screen_test.dart assert Privacy/Terms links.
- US-002 mock password reset: auth.service forgot/reset specs; auth-account.e2e-spec.ts forgot→reset→login; password_reset_screen.dart uses demoResetToken; password_reset_screen_test.dart email step.
- US-003 guest cart: cart_controller_test.dart (guest persistence, OOS blocks); cart.service.spec.ts merge qty cap + guest_wins; m3-shopper-flow.e2e-spec.ts cart/merge HTTP; cart_merge_service.dart + auth_notifier merge on login; checkout_models_test.dart forSession server cart after sign-in.
- US-004 merchandised home: home.service/controller specs; m3-api-contract.e2e-spec.ts GET /home; home_screen_test.dart banners/featured/new arrivals/categories; m3-seed.spec.ts US-004 category names; MockHomeRepository uses _defaultMerchandisedCategories().
- US-005 search/sort/filter: catalog.service.spec.ts, list-products.query.spec.ts, catalog_filters_test.dart, product_list_screen_test.dart; m2-catalog-contract.e2e-spec.ts + m3-api-contract flat pagination; m3-seed.spec.ts 50+ SKUs when USE_API_CATALOG/API seed (mock bundle ~12 SKUs offline).
- US-006 wishlist: wishlist.service.spec.ts import dedupe; wishlist_screen_test.dart guest list; auth_screen wishlist import dialog; m3-shopper-flow.e2e-spec.ts wishlist import.
- US-007 checkout quote US address/shipping/tax: checkout-pricing.service.spec.ts threshold 7500, flat 599, 8% tax; checkout_screen_test.dart review lines; checkout.controller + checkout.service Unauthorized when useServerCart without JWT.
- US-008 single coupon: checkout-pricing coupon rejection specs; checkout_notifier_test.dart stacking blocked; coupon_messages_test.dart.
- US-009 mock payment: orders.service.spec.ts cancel releases stock; m3-shopper-flow.e2e-spec.ts pending_payment→paid; mock_payment_screen_test.dart Pay now; mock_payment_notifier cancelOrder; no Stripe in payments.service MOCK provider.
- US-010 order history: orders_auth_redirect_test.dart guest→auth; orders_screen_test.dart list + detail lines; m3-shopper-flow listOrders 401 without auth; order.mapper.spec.ts summaries.
- US-011 status/tracking: order.mapper.spec.ts paid/fulfilled→processing, fulfilled+tracking→shipped; order_status_display_test.dart stepper + tracking visibility; m3-shopper-flow seeded SE-20261004-SHIP01 shipped detail.
- US-012 support/legal: account_screen_test.dart support email, form success; support.controller.spec.ts; checkout_screen legal links; supportEmail in StoreConfig seed.
- OpenAPI contract: openapi-contract-parity.spec.ts; openapi-controller-operation-ids.spec.ts (25 operationIds); infra/mobile-api-operations.spec.ts; health-openapi.e2e-spec.ts docs-json 503 on /health.
- Security: JwtAuthGuard on cart/wishlist/orders/users; checkout/orders create require auth for payment; secrets via JWT_SECRET env (environment.validation.spec.ts); test JWT secrets only in specs; forgotPassword omits demoResetToken when email unknown.

## Bugs
### BUG-001 [minor] docker compose up db fails without JWT_SECRET because api service env is validated (WI-021)
Steps: From repo root run `docker compose up -d db` without JWT_SECRET in the environment.
Expected: Postgres starts independently for local e2e/QA without requiring API staging secrets.
Actual: Compose fails during config interpolation: `JWT_SECRET is missing a value: Set JWT_SECRET in .env for staging` even when only the db service is requested.

### BUG-002 [minor] No integration_test package for critical shopper journeys (WI-021)
Steps: Inspect app/ for integration_test/ directory per Flutter conventions in milestone brief.
Expected: integration_test covers at least guest browse→cart→checkout→mock pay and login cart merge for emulator QA.
Actual: Coverage relies on widget tests and documented manual QA (reports/qa_M3_round1.md); no integration_test/ tree in the app package.
