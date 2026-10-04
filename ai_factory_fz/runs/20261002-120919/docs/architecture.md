# Architecture

SoftAura Skin Care M1 Speed Demo delivers a Flutter 3.x Android-first mobile app that browses a locally embedded mock catalog of 24 skincare SKUs across Body Wash, Cleansers, Moisturizers, and Face Care (curated third-party brands in the Olay Ultra Moisture Shea Butter Body Wash ~$12.99 / 1299 cents USD style), shows product detail with name, price, category, description, and rounded imagery, and supports an optional in-memory cart that clears on process restart. No backend, auth, payments, or checkout ship in M1—the app must launch on an Android emulator with mock data immediately. SoftAura visual tokens are fixed for implementation without approval gates: primary accent #7A9E8E (sage), warm ivory backgrounds, charcoal text, rounded product imagery. This document freezes the production-ready target architecture (NestJS + PostgreSQL 16 + Stripe) and a minimal OpenAPI 3.1 contract (health plus two catalog reads) so later milestones implement against an exact API and data model without guessing. Prices are integer USD cents with ISO 4217 currency; stock is per variant.

## Components
- **Flutter Mobile App (M1 primary)** (Flutter 3.x, Dart, Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, flutter_secure_storage (M2+), flutter_test, integration_test): Renders product list (browse), product detail, and optional in-memory cart. Embeds seeded SoftAura mock catalog of 24 SKUs for M1. Handles loading, empty, and error states; category association visible on list cards. SoftAura theme from design tokens (sage #7A9E8E, warm ivory, charcoal). Preserves list scroll/context when navigating back from detail. Post-M1 switches to generated OpenAPI client (dart-dio) against NestJS.
- **Local Mock Catalog (M1)** (assets/data/catalog.json, bundled image assets, Dart freezed models): Provides exactly 24 skincare SKUs across Body Wash, Cleansers, Moisturizers, and Face Care with name, brand, category, priceCents, currency USD, rounded image asset, description, and default-variant stock. Must include an Olay Ultra Moisture Shea Butter Body Wash style listing at 1299 cents USD. Source of truth for M1 browse/detail/cart; shapes mirror OpenAPI ProductSummary/ProductDetail for an easy M2 swap.
- **NestJS API Server (M2+)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Jest, Supertest): Contract-first REST API under global prefix /api/v1. Thin controllers, service-layer logic, PrismaService for data access. Catalog read endpoints first; auth, cart, orders, payments modules added after M1. DTOs use class-validator; responses match OpenAPI exactly.
- **PostgreSQL Database (M2+)** (PostgreSQL 16, Prisma ORM): System of record for users, catalog, carts, orders, and payment metadata. ACID transactions for stock reservation at checkout and order creation.
- **Stripe (later release)** (Stripe API, Stripe Flutter SDK, webhook signing secret): PaymentIntents in test mode; server creates intent, app confirms via Stripe SDK, webhook marks order paid. Card data never touches SoftAura servers.
- **Docker / CI (M2+)** (Docker, docker-compose, GitHub Actions): docker-compose for local/staging (API + Postgres). GitHub Actions runs lint, unit, and e2e tests on PR.

## Backend modules
### health
Liveness and database connectivity probe. Included in M1 OpenAPI contract; NestJS implementation deferred until backend work starts (does not block Flutter M1). Does not count toward the four API-operation cap.
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only SoftAura skincare catalog for browse and detail. Supports pagination, text search, and category filter (Body Wash, Cleansers, Moisturizers, Face Care). Product detail includes brand, description, category, and variants with per-variant price and stock. M1 Flutter uses local mock shaped like these responses; NestJS implements these two operations first in M2.
Entities: Category, Product, ProductVariant

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`

### auth (deferred post-M1)
Email/password registration and login, JWT access (15 min) and refresh tokens, account deletion. Out of M1 OpenAPI scope.
Entities: User, RefreshToken


### users (deferred post-M1)
Profile and saved shipping addresses for checkout. Out of M1 OpenAPI scope.
Entities: User, Address


### cart (deferred post-M1)
Signed-in user cart persisted server-side. M1 uses in-memory CartNotifier only; guest carts out of scope until a later release that explicitly requires guest checkout. Out of M1 OpenAPI scope.
Entities: Cart, CartItem


### orders (deferred post-M1)
Order placement and history with status lifecycle pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Order lines snapshot product name and unit price. Out of M1 OpenAPI scope.
Entities: Order, OrderItem


### payments (deferred post-M1)
Stripe PaymentIntents and webhooks; card data never on server. Out of M1 OpenAPI scope.
Entities: Payment, Order


## Mobile app features
- catalog: screens ProductListScreen (/products) — scrollable SoftAura product cards with name, formatted price from integer cents + USD (e.g. Olay Ultra Moisture Shea Butter Body Wash style as $12.99 from 1299 cents), rounded product imagery, category membership (Body Wash | Cleansers | Moisturizers | Face Care); warm ivory background, sage #7A9E8E accent, charcoal text; loading, empty, and error/retry states; all 24 seeded SKUs reachable by scroll, ProductDetailScreen (/products/:id) — name, brand, category, unit price (cents + USD), description, rounded product image; SoftAura styling; optional Add to cart (≥48dp); Android back returns to list with catalog still visible (state: CatalogRepository (M1: LocalCatalogDataSource from assets/data/catalog.json; M2+: generated CatalogApi). ProductListNotifier (AsyncNotifier) holds AsyncValue of the 24 products. ProductDetailNotifier loads one product by id. Price formatting helpers convert cents → display string without floats.)
- cart: screens CartScreen (/cart) — optional M1; line items with product name and unit price snapshot (cents + currency) copied at add time; session-only until process kill (state: CartNotifier (Notifier<CartState>) session-only in-memory for M1; clears on full process restart. Add from ProductDetailScreen. No persistence, auth, payment, or backend sync in M1.)
- core: screens  (state: Design tokens in lib/core/theme: primary #7A9E8E, warm ivory background, charcoal text, rounded imagery radii—chosen without style-approval gates; go_router routes /products, /products/:id, /cart; no live HTTP in M1 debug builds (offline mock). Debug Android cleartext only for 10.0.2.2 when backend arrives.)

## Data model
All monetary amounts are Int minor units (cents) with ISO 4217 currency code USD; never floats. Product is the merchandising parent (skincare listing with brand and category); ProductVariant is the purchasable SKU with its own priceCents, currency, and stockQuantity (and reservedQuantity for M2+ checkout holds). Listing cards show display price from the default or lowest active variant. Category is one of Body Wash, Cleansers, Moisturizers, Face Care (seeded as four Category rows; M1 mock associates each of 24 SKUs to exactly one). Flagship seed: Olay Ultra Moisture Shea Butter Body Wash style listing at 1299 cents USD displayed as $12.99. CartItem and OrderItem snapshot productName and unitPriceCents at write time so later catalog edits do not alter past carts/orders. Order.status: pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Stock reservation at checkout (M2+); failed or expired payment releases reserved stock. User.passwordHash uses bcrypt or argon2; support account deletion with PII removal/anonymization. M1 runtime uses only embedded mock catalog JSON—no Prisma/Postgres connection.

## Security
- M1 ships no auth, no mandatory network calls, and no PII, passwords, or payment data—mock catalog is read-only embedded data; do not send catalog or cart data to external payment providers in this increment.
- M2+ JWT bearer auth: access tokens 15-minute TTL, refresh tokens rotated and stored hashed server-side; flutter_secure_storage on mobile.
- Passwords hashed with bcrypt (cost ≥12) or argon2id; never store plaintext.
- All API input validated via class-validator DTOs; responses match OpenAPI schemas exactly; errors return { statusCode, error, message }.
- Stripe webhook verifies Stripe-Signature; idempotent event handling; card PAN/CVC never touch SoftAura servers.
- HTTPS-only in release mobile builds; debug Android allows cleartext to 10.0.2.2 only via network_security_config.
- Config and secrets via environment variables validated at NestJS startup (@nestjs/config)—never committed.
- Minimum personal data collection; account deletion removes or anonymizes PII.
- Catalog and health endpoints are public (security: []); bearerAuth scheme is declared for future protected modules.

## Architecture decisions
### ADR-001: Local embedded mock catalog for SoftAura M1 Speed Demo
**Context:** PRD requires the smallest runnable Flutter MVP on an Android emulator immediately with 24 skincare SKUs across four categories. NestJS, Postgres, generated clients, and CI would delay the demo. US-001/US-002/US-003 need browse, detail, and optional session cart only—no auth, payments, or checkout. Backend work is explicitly deferred if it slows delivery.

**Decision:** M1 loads 24 SoftAura Skin Care SKUs from assets (catalog.json + rounded image assets), including an Olay Ultra Moisture Shea Butter Body Wash style listing at 1299 cents USD. Category membership and price formatting run in-process. No HTTP client is required in M1 builds. CatalogRepository abstracts the data source so M2 can swap to the generated OpenAPI client without rewriting screens.

**Consequences:** Positive—offline demo, zero backend dependency, fastest path to validating SoftAura browse/detail UX. Negative—cart is session-only; no shared stock truth; M2 must migrate to API and keep server as source of truth for catalog and inventory.

### ADR-002: Integer minor units for all money fields
**Context:** Floating-point money causes rounding errors in totals and Stripe amounts. Project rules forbid floats for prices. Demo must show $12.99 from 1299 cents exactly for the body-wash style flagship listing.

**Decision:** Store and transmit all prices as integer cents with currency code USD (ISO 4217). Flutter, NestJS, Prisma Int, and OpenAPI integer schemas agree. Formatting to display strings (e.g. $12.99) happens only in the presentation layer; flutter_test covers cents → display.

**Consequences:** Positive—exact arithmetic, Stripe-compatible amounts, consistent contract. Negative—UI must use format helpers; developers must never use double for money.

### ADR-003: Contract-first OpenAPI 3.1 capped to M1 catalog operations
**Context:** Mobile convention requires a dart-dio client generated from OpenAPI. Hard scope limits this run to at most four API operations. Cart is in-memory and needs no API. Auth, payments, and checkout are out of scope. M1 prefers zero live business API dependency.

**Decision:** Freeze OpenAPI 3.1 with GET /health (infra, uncapped), GET /products (search, category filter, pagination), and GET /products/{productId}. Bearer auth is declared for M2+ but unused by these public operations. NestJS will implement controllers to match; Flutter generates packages/api_client when the backend ships. SoftAura visual tokens (#7A9E8E sage, warm ivory, charcoal) are fixed in the Flutter theme layer without stakeholder style approval.

**Consequences:** Positive—parallel M2 catalog work without over-building; mock models mirror schemas; generated types reduce drift; no approval gates block coding. Negative—later milestones must extend the same OpenAPI carefully; M1 cannot exercise a live API until NestJS exists.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.