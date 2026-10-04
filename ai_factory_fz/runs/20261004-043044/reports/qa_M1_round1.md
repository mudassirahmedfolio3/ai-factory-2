# QA report: M1

Result: **failed**

M1 guest shopping flows in app/ (shopease_app) pass 51 Flutter widget/unit tests and flutter analyze; NestJS Jest (5 tests) and api_client (113 tests) pass. OpenAPI in docs/ and apps/api match; only GET /api/v1/health is implemented on the API. Two major gaps: catalog seed never shows listing-level Out of stock badges, and GitHub CI validates apps/mobile instead of the delivered app/. US-006 API catalog consumption remains M2-deferred; local mock fallback works.

## Criteria checked
- US-001 home/listing UI: widget_test.dart, home_screen_test.dart, product_listing_screen_test.dart + catalog_repository_test (16 SKUs, 7 categories); ProductCard/PriceDisplay use integer pence via GbpMoneyFormatter
- US-001 category browse: home_screen_test + product_listing_screen_test (Ceiling Lights → filtered listing) + product_list_notifier_test applyRouteContext
- US-001 sale/list price: catalog_repository_test listing exposes compare-at pence; product_card_test sale badge
- US-001 Out of stock badge on listing: ProductCard supports OutOfStockBadge (product_card_test) but seed has zero products with inStock=false at summary level — not demonstrable in demo (BUG-001)
- US-002 search name/SKU/brand: catalog_repository_test, product_list_notifier_test, home_screen_test, product_listing_screen_test empty state + clear
- US-003 price filter: catalog_repository_test min/max pence
- US-003 brand/finish/wattage/availability filters: catalog_repository_test + filter UI in filter_sort_bottom_sheet.dart; product_list_notifier_test resetFilters
- US-003 popularity sort + tie-break: catalog_repository_test + catalog_query_engine_test (synthetic equal-rank tie-break)
- US-004 detail fields/specs/variants/reviews: product_detail_screen_test, product_detail_notifier_test, reviews_notifier_test, product_reviews_screen_test
- US-005 cart add/qty/remove/OOS: cart_notifier_test, cart_screen_test, product_detail_screen_test add/OOS variant
- US-006 M2 API catalog from NestJS: not in built WIs — only health endpoint exists; deferred
- US-006 local mock fallback: catalogRepositoryProvider uses LocalCatalogDataSource only (catalog_providers.dart); app launches without backend
- US-006 OpenAPI + Dart client: docs/openapi.yaml ≡ apps/api/openapi.yaml; GET /api/docs-json in main.ts; packages/api_client generated tests pass
- Backend OpenAPI alignment: HealthResponseDto matches HealthResponse schema; 503 ErrorResponse shape in health.service.ts
- Security: no committed API secrets found; health is public (security: [] in OpenAPI); catalog reads unauthenticated as specified

## Bugs
### BUG-001 [major] Listing never shows Out of stock badge in seeded demo (WI-003)
Steps: 1. Launch app on Android emulator. 2. Open Home featured carousel or Products tab listing. 3. Observe all 16 ProductCard tiles. Alternatively run: repository.listProducts(CatalogListQuery()) and check items.any((p) => !p.inStock). Seed only has variants with availableQuantity 0 while another variant remains in stock (e.g. assets/data/catalog.json CL-1001).
Expected: At least one listing card shows the Out of stock badge when the product has no purchasable variants (acceptance: badge when applicable).
Actual: All 16 ProductSummary.inStock values are true (variants.any inStock); OutOfStockBadge never appears on home or listing despite UI support in lib/core/widgets/product_card.dart.

### BUG-002 [major] CI Flutter job tests apps/mobile, not M1 deliverable app/ (WI-001)
Steps: 1. Open .github/workflows/ci.yml flutter job (working-directory: apps/mobile). 2. Compare with M1 implementation under app/ (shopease_app, 51 tests). 3. Run flutter test in apps/mobile — only bootstrap tests, not catalog/cart screens.
Expected: CI analyze/test gates the same Flutter app shipped for the M1 stakeholder demo.
Actual: CI runs against apps/mobile (lighting_retail_mobile stub); the full guest shopping app lives in app/ and is not exercised in CI.

### BUG-003 [minor] No Supertest e2e test for GET /api/v1/health (WI-001)
Steps: Search apps/api for test/e2e or supertest; only unit specs under src/health/*.spec.ts exist.
Expected: Per project conventions, Supertest e2e per controller verifying path, status 200/503, and response body shape.
Actual: Health is covered by mocked unit tests only; no HTTP-level e2e against the Nest application.

### BUG-004 [minor] app/README lacks M1/API readiness documentation (WI-001)
Steps: Read app/README.md — default Flutter template text only.
Expected: US-006: documentation notes local mock path and API readiness for follow-up integration (OpenAPI client in packages/api_client, staging URL).
Actual: Root README mentions API URLs; app/README (primary demo package) has no M1 or API-mode guidance.

### BUG-005 [minor] Filter reset preserves non-default sort (WI-004)
Steps: 1. On Products, open Filter & sort sheet. 2. Change sort to Price low–high and apply. 3. Open sheet again and tap Reset (calls ProductListNotifier.resetFilters in filter_sort_bottom_sheet.dart).
Expected: Reset filters to defaults including default popularity sort (CatalogListQuery.sort default popularity).
Actual: resetFilters rebuilds CatalogListQuery with sort: current.sort, so a changed sort survives reset; only filter fields clear.
