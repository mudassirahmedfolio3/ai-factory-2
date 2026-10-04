# QA report: M1

Result: **failed**

M1 delivers guest mock catalog browse, filters, detail with ratings/reviews/availability, and in-memory cart. Prior MoneyFormatter cents-jargon defect on detail is fixed. flutter analyze is clean; flutter test is 27/29 with two intentional AC failures. Major defect: product detail helper copy 'Tax-exclusive catalog price' violates US-005 shopper-readable jargon rule. Minors: global debug cleartext and undersized filter chips. No NestJS surface to OpenAPI-check. passed=false due to BUG-001.

## Criteria checked
- US-001 catalog list with name/image/price from integer minor units + ISO currency: MockCatalogRepository + ProductCard/MoneyFormatter; catalog_seed_test (12 products), product_list_screen_test, money_formatter_test; flutter test
- US-001 search/category/price filters update and clear: ProductListViewData.applyFilters + product_list_screen_test + catalog_filters_test
- US-002 list-to-detail with photos/name/description/availability/reviews: ProductDetailScreen + seed reviews; product_detail_screen_test, product_detail_seed_test, guest_shopping_journey_test
- US-002/US-005 shopper-readable price formatting via MoneyFormatter: PASS ($7.99); prior cents-jargon defect is fixed
- US-005 retail-readable copy on detail: FAIL — helper text 'Tax-exclusive catalog price' (product_detail_screen_test asserts absence)
- US-003 add-to-cart copies unitPriceCents; qty/subtotal update in memory: cart_controller_test, cart_screen_test, detail add-to-cart widget test, guest journey
- US-004 guest browse/detail/cart without sign-in; cart persists in session: app_router (no auth routes); guest_routes_test + guest_shopping_journey_test
- US-005 shared theme tokens on splash/list/detail/cart (<=6 screens): AppTheme/AppTokens; guest_routes_test route count; flutter analyze clean
- US-007 in-stock enables add-to-cart; out-of-stock disables: product_detail_screen_test + seed-product-10 unavailable
- US-008 category and price-band filters against seed bands: catalog_filters_test + catalog_seed_test + list filter widget test
- OpenAPI backend endpoints: N/A for M1 (no NestJS server; USE_API_CATALOG defaults false)
- Security: no secrets in code; AccessTokenStorage uses flutter_secure_storage; debug cleartext over-broad (usesCleartextTraffic=true)

## Bugs
### BUG-001 [major] Product detail shows technical 'Tax-exclusive catalog price' copy to shoppers (WI-003)
Steps: 1. Launch the Flutter app with mock catalog. 2. Open Shop catalog and tap Citrus Hand Soap (seed-product-1). 3. Read the helper text under the formatted price. 4. Reproduce: flutter test test/features/products/presentation/product_detail_screen_test.dart (fails expecting no 'Tax-exclusive'). Code: app/lib/features/products/presentation/product_detail_screen.dart lines 127-130.
Expected: Browse → detail → cart copy avoids technical jargon and stays readable for retail shoppers (US-005); price uses MoneyFormatter/PriceLabel only.
Actual: Detail shows helper text 'Tax-exclusive catalog price'. flutter analyze clean; flutter test: 27 passed, 2 failed (this assertion + cleartext).

### BUG-002 [minor] Debug Android manifest allows cleartext for all hosts, not only 10.0.2.2 (WI-001)
Steps: 1. Open app/android/app/src/debug/AndroidManifest.xml. 2. Note android:usesCleartextTraffic="true" alongside networkSecurityConfig. 3. Compare with app/android/app/src/debug/res/xml/network_security_config.xml (whitelists 10.0.2.2 only). 4. Reproduce: flutter test test/core/network/debug_cleartext_config_test.dart.
Expected: Debug builds allow cleartext only for 10.0.2.2 via network-security-config; release remains https-only.
Actual: Debug application sets usesCleartextTraffic=true globally, broadening cleartext beyond the 10.0.2.2-only convention.

### BUG-003 [minor] Category and price-band FilterChips lack 48dp minimum touch targets (WI-002)
Steps: 1. Open app/lib/features/products/presentation/product_list_screen.dart _FilterChipButton. 2. Observe FilterChip without BoxConstraints(minHeight: AppSpacing.xxl) or minimumSize 48. 3. Compare with variant ChoiceChips on ProductDetailScreen which set minHeight: AppSpacing.xxl (48).
Expected: Interactive controls meet the project minimum touch target of 48dp.
Actual: List filter chips use default Material FilterChip sizing (~32dp height) without a 48dp minimum constraint.
