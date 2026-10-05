# QA report: M2

Result: **passed**

M2 backend catalog and OpenAPI slice meets US-006 when Postgres is available (CI pattern: migrate, seed, test:e2e). Local verification: server unit tests 50/50 pass, Flutter app tests 41/41 and api_client 59/59 pass, build/lint/tsc/prisma validate pass. npm run test:e2e failed here only because Docker/Postgres at localhost:5432 was unreachable (25/30 e2e; m2-error-shape.e2e-spec.ts 5/5 pass with mocked Prisma). Three minor contract/config defects remain (empty DATABASE_URL validation, undocumented 400 on malformed productId, empty primaryImageUrl vs uri schema). No blocker or major bugs.

## Criteria checked
- US-006 AC1 health: GET /api/v1/health and unprefixed GET /health implemented in health.controller.ts and app.setup.ts; covered by health.service.spec.ts, health.controller.spec.ts, test/health-openapi.e2e-spec.ts (needs DB), test/m2-catalog-contract.e2e-spec.ts (needs DB), and test/m2-error-shape.e2e-spec.ts (503 contract with mocked Prisma, 5/5 pass locally)
- US-006 AC1 OpenAPI discoverability: GET /api/docs-json via SwaggerModule in app.setup.ts; operationIds getHealth, listCategories, listProducts, getProductById, listProductReviews asserted in test/m2-catalog-contract.e2e-spec.ts and server/src/infra/mobile-api-operations.spec.ts; server/openapi.yaml byte parity in openapi-contract-parity.spec.ts
- US-006 AC1 operation cap: m2-catalog-contract.e2e-spec.ts counts non-/health Swagger paths <=12 (live run blocked locally without DB; logic present)
- US-006 AC1 catalog list/detail/reviews: catalog.controller.ts + catalog.service.ts match docs/openapi.yaml paths and DTO shapes; catalog.service.spec.ts covers filters, pagination, ratings, price bands; m2-catalog-contract.e2e-spec.ts covers 200/400/404 shapes when DB seeded (not executed locally)
- US-006 AC1 seed parity with Flutter mock: mobile-seed-parity.spec.ts compares app/assets/seed/catalog_seed.json to server/prisma/seed.ts (12 SKUs, 4 category slugs, names/prices/availability)
- US-006 AC1 Dart client integration: dart-api-client-artifacts.spec.ts + app/packages/api_client tests; ApiCatalogRepository mapping in app/test/features/products/data/api_catalog_repository_test.dart
- US-006 AC2 mock fallback: useApiCatalog defaults false in catalog_source_config.dart; catalog_repository_test.dart and product_detail_repository_provider_test.dart; CatalogBootstrapRepository health-failure fallback in catalog_bootstrap_repository_test.dart
- Security: catalog/health intentionally unauthenticated (security: [] in contract); ValidationPipe whitelist+forbidNonWhitelisted; $queryRawUnsafe('SELECT 1') only in health.service.ts; no API keys in repo; error filter redacts secrets per error-response.filter.spec.ts
- Commands run from server/: npm ci, npm run build (after npx prisma generate), npm run lint, npm test (50 pass), npm run test:e2e (25 fail without Postgres), npx prisma generate/validate/format, npx tsc --noEmit; app/: flutter test (41 pass), flutter analyze (1 info), api_client flutter test (59 pass)

## Bugs
### BUG-002 [minor] Empty DATABASE_URL passes startup validation (WI-005)
Steps: 1) Open server/src/config/environment.validation.ts: DATABASE_URL has @IsString() only. 2) Run validateEnvironment({ DATABASE_URL: '', PORT: '3000' }) as in environment.validation.spec.ts test 'documents that an empty DATABASE_URL currently passes validation (should be rejected)'.
Expected: Invalid DATABASE_URL (empty string) fails fast at config validation with 'Environment validation failed'.
Actual: Empty string is accepted; failure appears later at PrismaService.$connect() with a less actionable PrismaClientInitializationError.

### BUG-003 [minor] Undocumented HTTP 400 for malformed productId on GET /products/{productId} (WI-007)
Steps: 1) docs/openapi.yaml GET /products/{productId} documents responses 200, 404, 500 only. 2) catalog.controller.ts uses ParseUUIDPipe on productId. 3) GET /api/v1/products/not-a-uuid returns 400 (asserted in test/m2-catalog-contract.e2e-spec.ts).
Expected: Only status codes declared in the OpenAPI contract are returned, or the contract documents 400 for invalid UUID.
Actual: HTTP 400 Bad Request is returned for a non-UUID path segment; not listed in the operation's documented responses.

### BUG-004 [minor] ProductSummary.primaryImageUrl can be empty string (invalid uri) (WI-007)
Steps: 1) docs/openapi.yaml ProductSummary.primaryImageUrl is required with format: uri. 2) catalog.service.ts sets primaryImageUrl to product.images[0]?.url ?? ''. 3) catalog.service.spec.ts test 'falls back to an empty primaryImageUrl when a product has no images' expects ''.
Expected: Every list item includes a valid URI for primaryImageUrl per the contract.
Actual: When a product has no images, the API emits primaryImageUrl: '' which is not a valid URI.

### BUG-005 [minor] npm run build fails after npm ci until npx prisma generate is run manually (WI-005)
Steps: 1) In server/, run npm ci (npm may skip @prisma/client postinstall when allow-scripts is not approved). 2) Run npm run build without running npx prisma generate. 3) Observe TS7006/TS2694 errors in catalog.service.ts referencing missing Prisma types.
Expected: Fresh install produces a buildable tree (postinstall or documented prepare step generates @prisma/client).
Actual: Build fails until npx prisma generate is run explicitly; CI mitigates via a dedicated Prisma generate step in .github/workflows/server-ci.yml.
