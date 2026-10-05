# Architecture

PulsePhones M1 (Speed Demo) delivers a Flutter 3.x Android-first smartphone storefront that browses a locally embedded mock catalog of 12–20 smartphones and shows product detail (name, USD price from integer cents, key details, star rating), with an optional in-memory cart that clears on process restart. No backend, auth, payments, or checkout ship in M1—the app must launch offline on an Android emulator immediately from seeded local data. This document freezes the production-ready target architecture (NestJS + PostgreSQL 16 + Stripe) and a minimal OpenAPI 3.1 contract (health plus two public catalog reads for US-001/US-002) so later milestones implement against an exact API and data model without guessing. Prices are integer USD cents with ISO 4217 currency; M1 assumes all seeded phones are in stock; star ratings are seeded display fields only.

## Components
- **Flutter Mobile App (M1 primary)** (Flutter 3.x, Dart, Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, flutter_secure_storage (M2+), flutter_test, integration_test): Renders PulsePhones-branded product list (browse), product detail, and optional in-memory cart. Embeds seeded mock smartphone catalog for M1. Handles loading, empty, and error states; list/detail run entirely against local data with no network. Post-M1 switches to generated OpenAPI client (dart-dio) against NestJS.
- **Local Mock Catalog (M1)** (assets/data/catalog.json, bundled image assets or placeholders, Dart freezed models): Provides 12–20 smartphone SKUs with name, priceCents, currency USD, key details/specs, seeded star rating, and image placeholder or asset. Source of truth for M1 browse/detail; shapes mirror OpenAPI ProductSummary/ProductDetail for an easy M2 swap.
- **NestJS API Server (M2+)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Jest, Supertest): Contract-first REST API under global prefix /api/v1. Thin controllers, service-layer logic, PrismaService for data access. Catalog read endpoints first; auth, cart, orders, payments modules added after M1. DTOs use class-validator; responses match OpenAPI exactly.
- **PostgreSQL Database (M2+)** (PostgreSQL 16, Prisma ORM): System of record for users, catalog, carts, orders, and payment metadata. ACID transactions for stock reservation at checkout and order creation.
- **Stripe (later release)** (Stripe API, Stripe Flutter SDK, webhook signing secret): PaymentIntents in test mode; server creates intent, app confirms via Stripe SDK, webhook marks order paid. Card data never touches PulsePhones servers.
- **Docker / CI (M2+)** (Docker, docker-compose, GitHub Actions): docker-compose for local/staging (API + Postgres). GitHub Actions runs lint, unit, and e2e tests on PR.

## Backend modules
### health
Liveness and database connectivity probe. Included in M1 OpenAPI contract; NestJS implementation deferred until backend work starts (does not block Flutter M1). Does not count toward the four API-operation cap.
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only smartphone catalog for browse and detail. Supports pagination. Product detail includes key details and star rating; variants carry per-variant price and stock for M2+. M1 Flutter uses local mock shaped like these responses; NestJS implements these two operations first in M2. Counts as two of at most four API operations.
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
Signed-in user cart persisted server-side. M1 uses in-memory CartNotifier only; guest carts out of scope. Out of M1 OpenAPI scope.
Entities: Cart, CartItem


### orders (deferred post-M1)
Order placement and history with status lifecycle pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Order lines snapshot product name and unit price. Out of M1 OpenAPI scope.
Entities: Order, OrderItem


### payments (deferred post-M1)
Stripe PaymentIntents and webhooks; card data never on server. Out of M1 OpenAPI scope.
Entities: Payment, Order


## Mobile app features
- catalog: screens ProductListScreen (/products) — scrollable PulsePhones-branded list of 12–20 smartphones with name, price formatted from integer USD cents (e.g. $899.99 for 89999), star rating summary, and image/placeholder; empty and error states, ProductDetailScreen (/products/:id) — name, USD price from integer cents, key details/specs, star rating; optional add-to-cart; back returns to list without losing local catalog state (state: CatalogRepository (M1: LocalCatalogDataSource from assets/data/catalog.json; M2+: generated CatalogApi). ProductListNotifier (AsyncNotifier) holds AsyncValue of products. ProductDetailNotifier loads one product by id from the same local seed.)
- cart (optional M1): screens CartScreen (/cart) — in-memory line items with product name, unit price snapshot (cents + USD), quantity increase/decrease/remove; empty state when cart has no lines (state: CartNotifier (Notifier<CartState>) session-only in-memory for M1; clears on full process restart. Add from ProductDetailScreen (stock assumed always available). No persistence, auth, or API in M1.)
- core: screens  (state: PulsePhones design tokens in lib/core/theme (agent-chosen, no style approval gate); go_router routes /products, /products/:id, /cart; no live HTTP in M1 debug builds (offline mock). Debug Android cleartext only for 10.0.2.2 when backend arrives.)

## Data model
All monetary amounts are Int minor units (cents) with ISO 4217 currency code USD; never floats. UI formats for display only. Product is the merchandising parent (smartphone model); ProductVariant is the purchasable SKU (e.g. storage + color) with its own priceCents, currency, and stockQuantity (plus reservedQuantity for M2+ checkout holds). M1 mock may use a single default variant per product with stock assumed always available. Listing and detail show seeded averageRating (and optional ratingCount) for social proof—review posting is out of scope. CartItem and OrderItem snapshot productName and unitPriceCents at write time so later catalog edits do not alter past carts/orders. Order.status: pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Stock reservation at checkout (M2+); failed or expired payment releases reserved stock. User.passwordHash uses bcrypt or argon2; support account deletion with PII removal/anonymization. M1 runtime uses only embedded mock catalog JSON—no Prisma/Postgres connection. Category is smartphones for this vertical.

## Security
- M1 ships no auth, no mandatory network calls, and no PII, passwords, or payment data—mock catalog is read-only embedded data.
- M2+ JWT bearer auth: access tokens 15-minute TTL, refresh tokens rotated and stored hashed server-side; flutter_secure_storage on mobile.
- Passwords hashed with bcrypt (cost ≥12) or argon2id; never store plaintext.
- All API input validated via class-validator DTOs; responses match OpenAPI schemas exactly; errors return { statusCode, error, message }.
- Stripe webhook verifies Stripe-Signature; idempotent event handling; card PAN/CVC never touch our servers.
- HTTPS-only in release mobile builds; debug Android allows cleartext to 10.0.2.2 only via network_security_config.
- Config and secrets via environment variables validated at NestJS startup (@nestjs/config)—never committed.
- Minimum personal data collection; account deletion removes or anonymizes PII.
- Catalog and health endpoints are public (security: []); bearerAuth scheme is declared for future protected modules.
- Accessibility: ≥48dp touch targets; semantic labels on list items and primary buttons.

## Architecture decisions
### ADR-001: Local embedded mock catalog for M1 Speed Demo
**Context:** PRD requires the smallest runnable Flutter MVP on an Android emulator in one sprint with browse and detail (optional cart). NestJS, Postgres, generated clients, and CI would delay the demo. US-001/US-002/US-003 need local catalog, detail, and session cart only—no auth or payments.

**Decision:** M1 loads 12–20 smartphones from embedded assets (catalog.json + images/placeholders). Browse, detail, and optional cart run in-process with zero commerce HTTP. CatalogRepository abstracts the data source so M2 can swap to the generated OpenAPI client without rewriting screens. Style tokens are chosen by the implementing agent without approval gates.

**Consequences:** Positive—offline demo, zero backend dependency, fastest path to validating browse→detail. Negative—cart is session-only; no shared stock truth; M2 must migrate to API and keep server as source of truth for catalog and inventory.

### ADR-002: Integer minor units for all money fields
**Context:** Floating-point money causes rounding errors in totals and Stripe amounts. Project rules forbid floats for prices; PRD example is 89999 cents → $899.99.

**Decision:** Store and transmit all prices as integer cents with currency code USD (ISO 4217). Flutter, NestJS, Prisma Int, and OpenAPI integer schemas agree. Formatting to display strings happens only in the presentation layer.

**Consequences:** Positive—exact math, Stripe-compatible amounts, consistent contract. Negative—developers must never use double for money; shared format helpers required in UI.

### ADR-003: Contract-first OpenAPI 3.1 limited to health and catalog reads
**Context:** Mobile convention mandates a dio client generated from OpenAPI; hard scope caps this run at four API operations. Must-have stories US-001/US-002 are satisfied by local mock in M1; cart is in-memory and needs no API. Prefer no backend work that slows the demo.

**Decision:** Freeze OpenAPI 3.1 now with GET /health (infra, uncapped), GET /products, and GET /products/{productId} only (two commerce operations). Bearer auth, pagination parameters, and ErrorResponse are declared for M2+. NestJS implements these controllers when backend work starts; Flutter generates packages/api_client then. Auth, cart, orders, and payments stay out of this document's paths.

**Consequences:** Positive—parallel M2 catalog work without over-building; mock models mirror ProductSummary/ProductDetail; stays within operation caps. Negative—M1 cannot exercise live API until NestJS ships; later milestones must extend the same OpenAPI file carefully.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.