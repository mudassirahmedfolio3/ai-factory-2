# QA report: M1

Result: **failed**

M1 guest shopping flows in app/ (shopease_app) pass 55 Flutter tests and flutter analyze; NestJS Jest (5) and packages/api_client (113) pass. OpenAPI in docs/ matches apps/api/openapi.yaml; GET /api/v1/health and GET /api/docs-json are implemented. One major defect remains: filter Reset does not restore default popularity sort (US-003). US-006 live catalog API consumption is M2-deferred; local mock path works.

## Criteria checked
- US-001 listing UI: widget_test.dart, home_screen_test.dart, product_listing_screen_test.dart, product_card_test.dart, gbp_money_formatter_test.dart; 16 products, 7 categories via catalog_repository_test
- US-001 Out of stock badge when applicable: Garden Bollard fully OOS in seed/catalog.json; catalog_repository_test inStock false; new product_listing_screen_test OutOfStockBadge on filtered card; product_card_test
- US-001 category browse: home_screen_test Ceiling Lights tap, product_listing_screen_test, product_list_notifier_test applyRouteContext
- US-001 sale/list integer pence: catalog_repository_test compare-at 5999/4999; product_card_test sale badge
- US-002 search name/SKU/brand: catalog_repository_test, product_list_notifier_test, home_screen_test CL-1001 routing, product_listing_screen_test empty state and Clear search
- US-003 price range filter: catalog_repository_test min/max pence
- US-003 brand/category/wattage/finish/availability filters: catalog_repository_test; filter_sort_bottom_sheet.dart UI; product_list_notifier_test clears filter fields on reset
- US-003 sort popularity + tie-break: catalog_repository_test, catalog_query_engine_test; new price ascending sort test in catalog_repository_test
- US-003 reset filters to defaults: ProductListNotifier.resetFilters keeps sort: current.sort (product_list_notifier.dart L85-91) — fails AC; product_list_notifier_test encodes preserved sort
- US-004 detail gallery/specs/variants/reviews: product_detail_screen_test, product_detail_notifier_test, reviews_notifier_test, product_reviews_screen_test, lighting_specs_table.dart conditional rows
- US-005 cart add/qty/remove/OOS: cart_notifier_test, cart_screen_test, product_detail_screen_test add and Out of stock variant
- US-006 API catalog from NestJS: not implemented (only HealthController); deferred M2 — not scored against built WIs
- US-006 local mock fallback: catalogRepositoryProvider → LocalCatalogDataSource only; app runs without backend
- US-006 OpenAPI + Dart client: identical openapi.yaml; main.ts /api/docs-json; api_client tests Money amountCents and GBP currency
- Backend contract: HealthResponseDto matches OpenAPI; 503 ErrorResponse in health.service.ts; docs/openapi.yaml byte-identical to apps/api/openapi.yaml
- Infra WI-001: debug network_security_config.xml cleartext 10.0.2.2 only; CI flutter job working-directory app/ guarded by flutter_ci_working_directory_test.dart
- Security: no committed API secrets; health public per OpenAPI security: []; global ValidationPipe whitelist on API

## Bugs
### BUG-001 [major] Filter Reset keeps non-default sort instead of restoring popularity default (WI-004)
Steps: 1. Launch app, open Products tab. 2. Open Filters and sort sheet, choose Price: low to high, Apply. 3. Reopen sheet, tap Reset (FilterSortBottomSheet._reset → ProductListNotifier.resetFilters). Alternatively run product_list_notifier_test.dart test 'ProductListNotifier reset filters keeps search and category route'.
Expected: Reset restores defaults including CatalogListQuery default sort popularity so listing order returns to merchandising rank.
Actual: resetFilters builds CatalogListQuery with sort: current.sort (app/lib/features/catalog/presentation/product_list_notifier.dart), so Price: low to high persists after Reset; unit test expects ProductSort.priceAsc to remain.

### BUG-002 [minor] No Supertest e2e test for GET /api/v1/health (WI-001)
Steps: Search apps/api for test/e2e or supertest usage; only src/health/*.spec.ts unit tests with mocked Prisma exist.
Expected: Per Nest conventions, HTTP-level e2e verifies GET /api/v1/health returns 200 with HealthResponse when DB up and 503 with ErrorResponse shape when DB down.
Actual: Health behavior is asserted only in mocked unit tests; no Supertest suite against Nest application.

### BUG-003 [minor] app/README lacks M1 local mock and API readiness notes (WI-001)
Steps: Read app/README.md — default Flutter template copy only.
Expected: US-006 documents that M1 uses assets/data/catalog.json via LocalCatalogDataSource, packages/api_client for M2, and staging base URL http://10.0.2.2:3000/api/v1.
Actual: app/README.md has generic getting-started text; API guidance exists only in repo root README.md.

### BUG-004 [minor] Root README still describes apps/mobile as the Flutter app (WI-001)
Steps: Read README.md line 3 and mobile networking link to apps/mobile/NETWORK_SECURITY.md.
Expected: Monorepo docs identify app/ (shopease_app) as the M1 deliverable and point Android cleartext config to app/android/app/src/debug.
Actual: README opening line lists Flutter mobile at apps/mobile; NETWORK_SECURITY.md path is under apps/mobile while M1 debug config lives under app/android.

### BUG-005 [minor] No integration_test for critical guest shopping journey (WI-001)
Steps: Glob app/integration_test — no files; only widget/unit tests under app/test/.
Expected: Per Flutter conventions, integration_test covers at least one end-to-end guest path (browse → detail → add to cart) on emulator.
Actual: Critical journey is covered by separate widget tests only; no integration_test directory.
