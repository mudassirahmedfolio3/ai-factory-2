# QA report: M1

Result: **failed**

M1 mostly delivers guest mock catalog browse, filters, detail with ratings/reviews/availability, and in-memory cart. flutter analyze is clean; flutter test is 24/25 with one intentional AC failure. Major defect: product detail does not use MoneyFormatter/PriceLabel and displays '799 cents USD' instead of '$7.99', breaking design-system consistency and US-005 readability. No NestJS surface in this milestone to OpenAPI-check. passed=false due to BUG-001.

## Criteria checked
- US-001 catalog list with name/image/price from integer minor units: verified via MockCatalogRepository + ProductCard MoneyFormatter; product_list_screen_test + catalog_seed_test (12 seeded products); flutter test
- US-001 search/category/price filters update and clear: product_list_controller.applyFilters + product_list_screen_test + catalog_filters_test
- US-002 list-to-detail navigation with photos/name/description/availability/reviews: product_detail_screen + seed reviews; guest_shopping_journey_test + product_detail_screen_test + product_detail_seed_test
- US-002 price display as shopper-readable PriceLabel from integer cents: FAIL — detail uses '_formatMinorPrice' -> '799 cents USD'; acceptance test expects MoneyFormatter '$7.99' and fails
- US-003 add-to-cart copies unit price cents and cart qty/subtotal update in memory: cart_controller_test + cart_screen_test + product_detail add-to-cart widget test + guest journey
- US-004 guest browse/detail/cart without sign-in; cart persists in session: app_router has no auth routes; guest_shopping_journey_test
- US-005 shared theme tokens on primary screens: AppTheme/AppTokens used by list/detail/cart/splash; analyze clean
- US-005 retail-readable copy on browse→detail→cart: FAIL on detail price jargon ('799 cents USD', 'Tax-exclusive catalog price')
- US-007 in-stock enables add-to-cart; out-of-stock disables: product_detail_screen_test + seed-product-10 unavailable
- US-008 category and price-band filters against seed bands: catalog_filters_test + catalog_seed_test + list filter widget test
- OpenAPI backend endpoints: N/A for M1 (no NestJS server in repo; Flutter mock path USE_API_CATALOG=false)
- Security: no secrets in code; tokens via flutter_secure_storage; debug cleartext config present but over-broad

## Bugs
### BUG-001 [major] Product detail price bypasses MoneyFormatter/PriceLabel and shows raw cents jargon (WI-003)
Steps: 1. Launch the Flutter app (mock catalog). 2. Open Shop catalog and tap Citrus Hand Soap (seed-product-1). 3. Observe the price text under the photo gallery. 4. Compare with the price shown on the product list card and cart after add. 5. Reproduce in tests: flutter test test/features/products/presentation/product_detail_screen_test.dart (fails expecting '$7.99'). Code: app/lib/features/products/presentation/product_detail_screen.dart _formatMinorPrice returns '$amountCents cents $currencyCode'.
Expected: Design system PriceLabel and list/cart consistency: integer cents formatted for shoppers (e.g. 799 + USD -> $7.99) via MoneyFormatter; copy remains retail-readable (US-005).
Actual: Detail screen shows '799 cents USD' and label 'Tax-exclusive catalog price'. List/cart correctly show '$7.99'. flutter test: 24 passed, 1 failed on this assertion.

### BUG-002 [minor] Debug Android manifest allows cleartext for all hosts, not only 10.0.2.2 (WI-001)
Steps: 1. Open app/android/app/src/debug/AndroidManifest.xml. 2. Note android:usesCleartextTraffic="true" alongside networkSecurityConfig. 3. Compare with app/android/app/src/debug/res/xml/network_security_config.xml which only whitelists 10.0.2.2.
Expected: Debug builds allow cleartext only for 10.0.2.2 via network-security-config; release remains https-only.
Actual: Debug application sets usesCleartextTraffic=true globally, broadening cleartext beyond the 10.0.2.2-only convention.

### BUG-003 [minor] Product detail shows technical 'Tax-exclusive catalog price' copy to shoppers (WI-003)
Steps: 1. Open any product detail screen. 2. Read the helper text under the price.
Expected: Browse→detail→cart copy avoids technical jargon and stays readable for retail shoppers (US-005).
Actual: Helper text reads 'Tax-exclusive catalog price', which is tax/commerce jargon unsuitable for a non-technical demo shopper UI.
