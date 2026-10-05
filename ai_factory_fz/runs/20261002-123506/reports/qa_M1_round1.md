# QA report: M1

Result: **passed**

M1 QA for built WI-001 only: NestJS /api/v1 getHealth, listProducts, and getProductById match the frozen OpenAPI contract (paths, methods, status codes, ErrorResponse/HealthResponse/ProductListResponse/ProductDetail shapes), serve 16 jewellery stub SKUs with Tropical Earring at 1999 USD cents, support search/filters/pagination/reviews, validate query/path input, and keep catalog/health public with env-validated config and no secrets in code. Existing unit/e2e tests plus newly added validation/filter/empty-review/SKU-count cases document that coverage; sandbox test execution was unavailable in this run so results are from static review. Flutter US-001/US-002 demo path remains blocked by failed WI-002–WI-005 (api_client serializer build failure cascading to list/detail/cart); those work items are out of bug scope here, so no blocker/major defects were filed and passed is true for the WI-001 gate.

## Criteria checked
- WI-001 OpenAPI freeze: GET /health (getHealth) path, security:[], 200 HealthResponse {status,database,timestamp} and 503 ErrorResponse {statusCode,error,message} match server/openapi.yaml and docs/openapi.yaml; NestJS HealthController/HealthService probe PrismaService.isDatabaseUp and throw ServiceUnavailableException with that shape — covered by health.service.spec.ts and catalog.e2e-spec.ts GET /api/v1/health
- WI-001 OpenAPI freeze: GET /products (listProducts) supports page, pageSize, q, category, metal, occasion, minPriceCents, maxPriceCents, sort; 200 ProductListResponse {items,total,page,pageSize}; 400 ErrorResponse — implemented in CatalogController/CatalogService + ListProductsQueryDto (class-validator); covered by catalog.service.spec.ts and catalog.e2e-spec.ts
- WI-001 OpenAPI freeze: GET /products/{productId} (getProductById) returns ProductDetail with description, reviews, variants, averageRating, inStock; Tropical Earring id b2222222-2222-4222-8222-222222222201 at price.amountCents=1999 currency=USD; 404 ErrorResponse for unknown UUID — covered by catalog.service.spec.ts and catalog.e2e-spec.ts
- WI-001 stub catalog: 16 in-memory SKUs (within 12–20), search case-insensitive on name/searchableText, AND filters for category/metal/occasion/price, empty items+total=0 when no match — catalog.stub-data.ts + CatalogService.listProducts tests
- WI-001 security/config: catalog and health are public (security:[]); no auth/payments endpoints; ConfigModule validates DATABASE_URL at startup; no API secrets hardcoded in server/src; errors normalized via HttpErrorFilter to {statusCode,error,message}; global prefix /api/v1
- US-001 Given Flutter seeded catalog shows Tropical Earring $19.99 and scrollable list — NOT verifiable against built items; depends on failed WI-002/WI-003 (no bug filed per instructions)
- US-001 Given search query Tropical filters list and clear restores — NOT verifiable; depends on failed WI-002/WI-003 (no bug filed)
- US-001 Given price/category/metal/occasion filters and clear — NOT verifiable; depends on failed WI-002/WI-003 (no bug filed)
- US-001 Given empty filtered set shows empty state — NOT verifiable; depends on failed WI-002/WI-003 (no bug filed)
- US-002 Given tap product opens detail with name/description/price/category/metal/occasion/stock — NOT verifiable; depends on failed WI-003/WI-004 (no bug filed)
- US-002 Given mock reviews show aggregate stars and review list or empty reviews state — NOT verifiable; depends on failed WI-004 (no bug filed); API stub does return reviews for Tropical Earring and empty reviews for Rose Petal Bracelet
- US-002 Given back navigation preserves search/filter state — NOT verifiable; depends on failed WI-002/WI-004 (no bug filed)

## Bugs
None.