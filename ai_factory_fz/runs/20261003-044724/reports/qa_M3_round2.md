# QA report: M3

Result: **failed**

Backend unit tests (119/119), backend e2e (16 passed, 25 skipped without E2E_DATABASE_AVAILABLE=1 and Postgres), flutter analyze (clean), and flutter test (64/64) all succeeded. OpenAPI parity specs (server vs docs byte-identical, 24 M3 operationIds, live Swagger) passed without a database. One blocker remains: guest shoppers can reach checkout and mock payment, but createOrder/completeMockPayment require JWT per OpenAPI and OrdersController, so guests cannot finish purchase despite the milestone and PRD guest persona requiring checkout without registration. Added one backend unit test for cancelOrder stock release (US-009).

## Criteria checked
- US-001 register/login/logout: server auth.service.spec.ts (bcrypt passwordHash, tokens), auth-account.e2e-spec.ts (full flow, skipped without DB); app token_storage_test.dart, auth_screen_test.dart (legal links), auth_validators_test.dart; openapi-contract-parity + auth controller specs.
- US-001 legal placeholders: auth_screen_test.dart and account_screen_test.dart assert Privacy Policy and Terms of Sale; routes in app_router.dart LegalDocumentScreen; checkout_screen legal TextLinkButtons (manual/code review).
- US-002 mock password reset: auth-account.e2e-spec.ts forgot/reset/login; password_reset_screen_test.dart email step; auth.service.spec.ts demoResetToken behavior.
- US-003 guest cart: cart_controller_test.dart (lines, cents, OOS block, guest persistence); cart_screen_test.dart; cart.service.spec.ts merge + guest_wins; m3-shopper-flow.e2e-spec.ts cart/merge (DB-gated); cart_merge_service.dart + auth_notifier merge on login.
- US-003 signed-in cart restore: cart_controller _load uses ApiCartRepository.getCart when authenticated (code); e2e merge flow validates API persistence when DB available.
- US-004 merchandised home: home_screen_test.dart (banners, featured, new arrivals, categories); home.service.spec.ts; m3-seed.spec.ts asserts five launch category names in seed.
- US-004 navigation from home: home_screen.dart navigation (code); home_screen_test scroll/tap categories and products with fake repo.
- US-005 search/sort/filter: catalog_filters_test.dart; list-products.query.spec.ts; m2-catalog-contract.e2e-spec.ts + m3-api-contract.e2e-spec.ts (DB-gated); product_list_screen_test.dart; api_catalog_repository_test.dart.
- US-005 OOS in list/detail: cart_controller_test.dart; product_detail_screen.dart blocks add when unavailable (code); catalog_seed_test.dart unavailable SKU.
- US-006 guest wishlist: wishlist_screen_test.dart; guest_wishlist_storage.dart secure storage; wishlist.service.spec.ts import dedupe (server).
- US-006 signed-in wishlist + import: wishlist_notifier.dart importGuestWishlistIfNeeded; m3-shopper-flow.e2e-spec.ts wishlist import (DB-gated).
- US-007 checkout quote/totals: checkout-pricing.service.spec.ts (599 shipping below 7500, free shipping, 8% tax); checkout_screen_test.dart review lines; checkout_notifier debounced quote (code).
- US-008 coupons: checkout-pricing.service.spec.ts validation paths; coupon_messages_test.dart; checkout_notifier_test.dart stacking block.
- US-009 mock payment: m3-shopper-flow.e2e-spec.ts checkout→createOrder→completeMockPayment (DB-gated); mock_payment_screen_test.dart; payments.service.spec.ts MOCK provider; new orders.service.spec.ts cancel releases reservedQuantity.
- US-010 order history: orders_auth_redirect_test.dart guest→auth; orders_screen_test.dart list/empty; m3-shopper-flow seeded list (DB-gated); orders.service getOrderById user scoping.
- US-011 tracking/stepper: order_status_display_test.dart; order.mapper.spec.ts shopperStatus mapping; orders_screen_test.dart stepper; seeded SE-20261004-SHIP01 e2e (DB-gated).
- US-012 support/legal: account_screen_test.dart support email, form success; support.controller.spec.ts; checkout legal links (code).
- OpenAPI contract: openapi-contract-parity.spec.ts, mobile-api-operations.spec.ts, m3-openapi-surface.e2e-spec.ts, openapi-controller-operation-ids.spec.ts, dart-api-client-artifacts.spec.ts.
- Security review: JwtAuthGuard on cart/wishlist/orders/users; OptionalJwtAuthGuard on checkout/support; JWT_SECRET from env (environment.validation.spec.ts); no production secrets in src; forgot-password omits demoResetToken for unknown emails (auth.service.spec.ts).

## Bugs
### BUG-001 [blocker] Guest shoppers cannot complete checkout because order APIs require authentication (WI-018)
Steps: 1. Launch app as guest (no login). 2. Add an in-stock item to cart. 3. Cart → Proceed to checkout. 4. Enter valid US address, continue to review, then Continue to payment. 5. MockPaymentNotifier.initializeFromDraft calls POST /api/v1/orders without a bearer token (OrdersController @UseGuards(JwtAuthGuard); OpenAPI documents 401).
Expected: Per milestone scope and PRD First-time Guest Shopper, guest can complete US checkout with mock payment without registering; or UI must require sign-in before payment with clear guidance.
Actual: Guest can obtain checkout quotes (OptionalJwtAuthGuard) but order creation fails with 401 Unauthorized; mock payment screen shows error phase and no confirmation order number.
