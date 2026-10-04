# QA report: M1

Result: **passed**

M1 passes acceptance criteria: guest mock catalog browse/search/filters, detail with ratings/reviews/availability, and in-memory cart all work. Prior major defects (cents/Tax-exclusive jargon, global cleartext) are fixed. flutter analyze clean; flutter test 30/30. Added a 48dp filter-chip touch-target test (passes via Material tap targets). No NestJS surface to OpenAPI-check. Two minor polish issues only; passed=true.

## Criteria checked
- US-001 catalog list name/image/price from integer minor units + ISO currency: MockCatalogRepository + ProductCard/MoneyFormatter; catalog_seed_test (12 products), product_list_screen_test, money_formatter_test; flutter test passed
- US-001 search/category/price filters update and clear: ProductListViewData.applyFilters + product_list_screen_test + catalog_filters_test
- US-002 list-to-detail with photos/name/description/availability/price via MoneyFormatter: ProductDetailScreen; product_detail_screen_test + guest_shopping_journey_test
- US-002 aggregate star rating + review entries match seed: product_detail_seed_test + product_detail_screen_test (seed-product-1 / Maya review)
- US-003 add-to-cart copies unitPriceCents; qty/subtotal update in memory: cart_controller_test, cart_screen_test, detail add-to-cart widget test, guest journey
- US-004 guest browse/detail/cart without sign-in; cart persists in session: app_router (no auth routes); guest_routes_test + guest_shopping_journey_test
- US-005 shared theme tokens on splash/list/detail/cart (<=6 screens): AppTheme/AppTokens; guest_routes_test route count; flutter analyze clean
- US-005 retail-readable price/copy on detail path: MoneyFormatter $7.99; no Tax-exclusive/cents jargon; product_detail_screen_test asserts absence
- US-007 in-stock enables add-to-cart; out-of-stock disables: product_detail_screen_test + seed-product-10 unavailable
- US-008 category and price-band filters against seed bands: catalog_filters_test + catalog_seed_test + list filter widget test + new 48dp chip touch-target test
- OpenAPI NestJS endpoints: N/A for M1 (no NestJS server; USE_API_CATALOG defaults false; mock path works)
- Security: no secrets in code; AccessTokenStorage uses flutter_secure_storage; debug cleartext limited to 10.0.2.2 via network_security_config; debug_cleartext_config_test passed

## Bugs
### BUG-001 [minor] Cart badge uses hard-coded sizes instead of design tokens (WI-004)
Steps: 1. Open app/lib/features/cart/presentation/cart_action_button.dart. 2. Inspect the item-count badge Positioned/Container: right/top -6, padding 4/2, BorderRadius.circular(10), minWidth/minHeight 18. 3. Compare with AppSpacing/AppRadii tokens in app/lib/core/theme/app_tokens.dart.
Expected: Widget sizes and radii come from shared design tokens (AppSpacing/AppRadii); no hard-coded numeric sizes in feature widgets.
Actual: CartActionButton badge uses literal pixel values (-6, 4, 2, 10, 18) instead of AppSpacing/AppRadii, breaking the no hard-coded sizes convention while remaining functionally correct.

### BUG-002 [minor] Cart summary shows incorrect plural for a single item (WI-004)
Steps: 1. Launch the app and add one available product to the cart. 2. Open the cart screen (/cart). 3. Read the summary bar item-count text. 4. Reproduce: flutter test test/features/cart/presentation/cart_screen_test.dart (expects text '1 items'). Code: cart_screen.dart '${state.itemCount} items'.
Expected: Retail-readable copy uses correct pluralization (e.g. '1 item' / '2 items').
Actual: Summary always appends 'items', so a single-line cart shows '1 items'.
