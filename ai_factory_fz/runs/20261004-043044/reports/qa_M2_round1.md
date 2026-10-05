# QA report: M2

Result: **passed**

Verified M2 catalog slice and Flutter API client integration: apps/api Jest 57/57 and nest build pass after npx prisma generate; app flutter test 62/62, flutter analyze clean (after fixing deprecated Finder.description in integration_test), api_client 113/113; OpenAPI byte-parity and eight operationIds covered by openapi.contract.spec.ts and openapi-contract.e2e-spec.ts; app/assets/data/catalog.json and apps/api/prisma/data/catalog.json are identical (SHA256 0F61A712…). One minor local-dev gap: npm ci alone leaves Prisma client unstubs until npx prisma generate (CI already runs generate). Live API smoke (scripts/staging-smoke.mjs) was not executed here because no Docker stack was running.

## Criteria checked
- US-001 home/listing UI: widget_test.dart, home_screen_test.dart, product_listing_screen_test.dart, product_card_test.dart (GBP pence, out-of-stock badge)
- US-001 category browse path: product_listing_screen_test.dart Category navigation; product_list_notifier_test.dart applyRouteContext
- US-001 integer pence pricing: gbp_money_formatter_test.dart, catalog_repository_test.dart listing exposes sale compare-at
- US-002 search by name: product_list_notifier_test.dart, product_listing_screen_test.dart Inline search
- US-002 search by SKU/brand: catalog_repository_test.dart search by product name and SKU; catalog-product.filters.spec.ts
- US-002 empty search state: product_list_notifier_test.dart, product_listing_screen_test.dart
- US-003 price range filter: catalog_repository_test.dart price filter; catalog-product.filters.spec.ts
- US-003 multi-facet filters and reset: catalog_repository_test.dart brand/finish/wattage/inStockOnly; product_list_notifier_test.dart reset filters
- US-003 popularity sort: catalog_query_engine_test.dart, catalog_repository_test.dart, catalog-product.filters.spec.ts sortProductsForListing
- US-004 detail fields: product_detail_screen_test.dart, product_detail_notifier_test.dart, catalog_repository_test.dart product detail
- US-004 lighting specs: product_detail_screen_test.dart specs section; catalog.mapper.spec.ts backend
- US-004 variants/reviews/OOS add-to-cart: product_detail_screen_test.dart variant and cart tests; reviews_notifier_test.dart
- US-005 add to cart snapshot: product_detail_screen_test.dart Add to cart adds snapshot line
- US-005 quantity/subtotal/remove: cart_notifier_test.dart, cart_screen_test.dart
- US-005 OOS blocked: product_detail_screen_test.dart Selecting out-of-stock variant disables add to cart
- US-006 API health/catalog ops: catalog.e2e-spec.ts all seven catalog ops + health.e2e-spec.ts; PUBLIC_CATALOG_OPERATIONS registry
- US-006 mock fallback: catalog_repository_fallback_test.dart; app/docs/DEMO_RUNBOOK.md; integration_test/guest_catalog_flow_test.dart local overrides
- US-006 OpenAPI Money GBP integer: openapi.contract.spec.ts Money schema; catalog.e2e-spec.ts GBP amountCents
- Contract paths/methods: openapi.contract.spec.ts docs vs apps/api openapi.yaml byte parity; openapi-contract.e2e-spec.ts GET /api/docs-json
- Security: catalog routes unauthenticated by design (guest M2); ParseUUIDPipe on product ids (new e2e 400); ValidationPipe whitelist/forbidNonWhitelisted in main.ts; no API keys in source; .env.example uses localhost placeholder only

## Bugs
### BUG-001 [minor] npm ci leaves Prisma Client ungenerated until manual prisma generate (WI-007)
Steps: From apps/api run: npm ci. Then npm test or npm run build without running npx prisma generate.
Expected: Install produces a usable @prisma/client (via postinstall or documented npm script) so build and tests pass immediately after ci.
Actual: Jest e2e/unit and nest build fail with TypeError/TS2305 (Prisma.SortOrder undefined, missing model exports) until npx prisma generate is run manually. GitHub Actions mitigates with an explicit generate step; hardened npm allow-scripts can skip @prisma/client postinstall.
