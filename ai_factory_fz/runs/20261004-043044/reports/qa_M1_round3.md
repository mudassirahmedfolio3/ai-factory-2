# QA report: M1

Result: **passed**

M1 guest shopping flows meet acceptance criteria: 56 Flutter tests and flutter analyze pass; NestJS Jest (5) and api_client (113) pass. Implemented GET /api/v1/health and GET /api/docs-json match OpenAPI (SHA256-identical docs/openapi.yaml and apps/api/openapi.yaml). Local mock catalog (16 SKUs) drives all UI; US-006 live catalog HTTP reads remain M2. No blocker or major defects; four minor documentation and test-harness gaps remain.

## Criteria checked
- US-001 client-ready UI: widget_test.dart (Lumen home), app_shell_test.dart (no Flutter Demo), home_screen_test.dart, product_listing_screen_test.dart, product_card_test.dart
- US-001 product cards image/name/GBP price: ProductCard + PriceDisplay + gbp_money_formatter_test.dart; listing shows £ via product_listing_screen_test.dart
- US-001 Out of stock badge: Garden Bollard inStock false in catalog_repository_test.dart; OutOfStockBadge in product_listing_screen_test.dart and product_card_test.dart
- US-001 12–20 seeded products: catalog_repository_test.dart and loads catalog.json asset (16 products); default_catalog_seed.dart
- US-001 taxonomy browse: 7 CategoryTile widgets in home_screen_test.dart; ceiling-lights route in product_listing_screen_test.dart and product_list_notifier_test.dart
- US-001 sale/list integer pence: catalog_repository_test.dart compareAt 5999/4999; product_card_test.dart sale badge
- US-002 search by name: catalog_repository_test.dart and product_list_notifier_test.dart Modern LED Ceiling Light
- US-002 search by SKU/brand: catalog_repository_test.dart CL-1001 and Luminex; home_screen_test.dart CL-1001 routing
- US-002 empty search + clear: product_list_notifier_test.dart; product_listing_screen_test.dart empty state and Clear search
- US-003 price range filter GBP pence: catalog_repository_test.dart min/maxPriceCents
- US-003 brand/category/wattage/finish/availability filters: catalog_repository_test.dart; FilterSortBottomSheet UI in filter_sort_bottom_sheet.dart; inStockOnly test
- US-003 popularity sort rank then 90-day units: catalog_repository_test.dart; catalog_query_engine_test.dart tie-break and unset rank
- US-003 price sort: catalog_repository_test.dart priceAsc
- US-003 reset filters to defaults including popularity sort: ProductListNotifier.resetFilters uses fresh CatalogListQuery (default sort); product_list_notifier_test.dart reset tests including listing order
- US-004 detail name/SKU/price/stock/gallery/description: product_detail_screen_test.dart
- US-004 conditional lighting specs: lighting_specs_table.dart omits empty fields; product_detail_screen_test.dart Wattage 24W IP44
- US-004 variants/ratings/reviews/OOS add state: product_detail_notifier_test.dart; product_detail_screen_test.dart variant Matte Black Out of stock; reviews_notifier_test.dart and product_reviews_screen_test.dart
- US-005 add to cart snapshot: cart_notifier_test.dart and product_detail_screen_test.dart
- US-005 qty/remove/subtotal: cart_notifier_test.dart and cart_screen_test.dart
- US-005 block OOS add: cart_notifier_test.dart does not add out-of-stock variant; product_detail_screen_test.dart disabled button
- US-006 live API catalog parity: not in M1 scope (AppModule only HealthModule); deferred M2 — not scored against delivered WIs
- US-006 local mock without backend: catalogRepositoryProvider → LocalCatalogDataSource only; app runs with catalogTestOverrides in tests
- US-006 OpenAPI + generated client: identical openapi.yaml copies; main.ts serves /api/docs-json; packages/api_client catalog and health API tests
- Backend contract: HealthResponseDto fields match OpenAPI; health.service.ts 503 ErrorResponse shape; global prefix api/v1; ValidationPipe whitelist
- WI-001 Android debug cleartext 10.0.2.2 only: app/android/app/src/debug/res/xml/network_security_config.xml; release manifest has no cleartext override
- Security: no committed .env or API keys in source; health endpoint security [] per OpenAPI

## Bugs
### BUG-001 [minor] No Supertest e2e test for GET /api/v1/health (WI-001)
Steps: Search apps/api for test/e2e or supertest; only src/health/*.spec.ts with mocked Nest decorators and Prisma exist.
Expected: HTTP-level e2e verifies GET /api/v1/health returns 200 HealthResponse when DB is up and 503 {statusCode,error,message} when DB is down.
Actual: Health behavior is covered only by unit tests with mocks; no Supertest suite bootstraps the Nest application.

### BUG-002 [minor] app/README lacks M1 mock catalog and API readiness notes (WI-001)
Steps: Read app/README.md.
Expected: Documents M1 LocalCatalogDataSource + assets/data/catalog.json, packages/api_client for M2, and debug base URL http://10.0.2.2:3000/api/v1 per US-006.
Actual: app/README.md is default Flutter template text; API guidance lives only in repo root README.md.

### BUG-003 [minor] Root README still points mobile app at apps/mobile (WI-001)
Steps: Read README.md line 3 and mobile networking link to apps/mobile/NETWORK_SECURITY.md.
Expected: Monorepo docs identify app/ (shopease_app) as the M1 Flutter deliverable and Android cleartext config under app/android/app/src/debug.
Actual: README opens with Flutter at apps/mobile and links NETWORK_SECURITY.md under apps/mobile while M1 config is under app/android.

### BUG-004 [minor] No integration_test for guest browse-to-cart journey (WI-001)
Steps: Glob app/integration_test — directory absent; coverage is split across widget/unit tests only.
Expected: Per Flutter conventions, integration_test exercises at least one emulator journey (browse → detail → add to cart) for M1 demo confidence.
Actual: No integration_test target; journeys validated by separate widget tests (home, listing, detail, cart).
