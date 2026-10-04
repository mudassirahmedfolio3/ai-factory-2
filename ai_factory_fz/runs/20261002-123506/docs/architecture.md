# Architecture

Womens Jewellery M1 Speed Demo delivers a Flutter 3.x Android-first mobile app that browses a locally embedded mock catalog of ~12–20 fashion jewellery SKUs (earrings, necklaces, bracelets, rings), including Tropical Earring at 1999 cents USD, shows product detail with metal, occasion, stock, aggregate star rating and mock reviews, and supports a simple in-memory cart with quantity updates that clears on process restart. No backend, auth, payments, or checkout ship in M1—the app must launch on an Android emulator with mock data immediately. Style tokens may be chosen by the implementation agent without approval gates. This document freezes the production-ready target architecture (NestJS + PostgreSQL 16 + Stripe) and a minimal OpenAPI 3.1 contract (health plus two catalog reads) so later milestones implement against an exact API and data model without guessing. Prices are integer USD cents with ISO 4217 currency; stock is per variant.

## Components
- **Flutter Mobile App (M1 primary)** (Flutter 3.x, Dart, Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, flutter_secure_storage (M2+), flutter_test, integration_test): Renders product list (browse with search and filters), product detail (reviews and star ratings), and in-memory cart with quantity steppers. Embeds seeded Womens Jewellery mock catalog for M1. Handles loading, empty, and error states; preserves list search/filter when navigating back from detail. Post-M1 switches to generated OpenAPI client (dart-dio) against NestJS.
- **Local Mock Catalog (M1)** (assets/data/catalog.json, bundled image assets, Dart freezed models): Provides ~12–20 jewellery SKUs with name, description, category, metal, occasion, priceCents, currency USD, primary image or placeholder, default-variant stock, averageRating, and mock reviews. Must include Tropical Earring at 1999 cents USD. Source of truth for M1 browse/detail/cart; shapes mirror OpenAPI ProductSummary/ProductDetail for an easy M2 swap.
- **NestJS API Server (M2+)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Jest, Supertest): Contract-first REST API under global prefix /api/v1. Thin controllers, service-layer logic, PrismaService for data access. Catalog read endpoints first; auth, cart, orders, payments modules added after M1. DTOs use class-validator; responses match OpenAPI exactly.
- **PostgreSQL Database (M2+)** (PostgreSQL 16, Prisma ORM): System of record for users, catalog, reviews, carts, orders, and payment metadata. ACID transactions for stock reservation at checkout and order creation.
- **Stripe (later release)** (Stripe API, Stripe Flutter SDK, webhook signing secret): PaymentIntents in test mode; server creates intent, app confirms via Stripe SDK, webhook marks order paid. Card data never touches Womens Jewellery servers. Post-M1 confirmation email from orders@womensjewellery.demo.
- **Docker / CI (M2+)** (Docker, docker-compose, GitHub Actions): docker-compose for local/staging (API + Postgres). GitHub Actions runs lint, unit, and e2e tests on PR.

## Backend modules
### health
Liveness and database connectivity probe. Included in M1 OpenAPI contract; NestJS implementation deferred until backend work starts (does not block Flutter M1). Does not count toward the four API-operation cap.
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only Womens Jewellery catalog for browse and detail. Supports pagination, text search, price range, category (earrings, necklaces, bracelets, rings), metal (gold-tone, silver-tone, rose-gold), and occasion (everyday, work, gift, party). Product detail includes description, metal, occasion, variants with per-variant price/stock, averageRating, and reviews. M1 Flutter uses local mock shaped like these responses; NestJS implements these two operations first in M2.
Entities: Category, Product, ProductVariant, Review

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`

### auth (deferred post-M1)
Email/password registration and login, JWT access (15 min) and refresh tokens, account deletion. Out of M1 OpenAPI scope.
Entities: User, RefreshToken


### users (deferred post-M1)
Profile and saved shipping addresses for checkout. Out of M1 OpenAPI scope.
Entities: User, Address


### cart (deferred post-M1)
Signed-in user cart persisted server-side. M1 uses anonymous in-memory CartNotifier only; guest vs signed-in cart ownership deferred. Out of M1 OpenAPI scope.
Entities: Cart, CartItem


### orders (deferred post-M1)
Order placement and history with status lifecycle pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Order lines snapshot product name and unit price. Confirmation email brand Womens Jewellery from orders@womensjewellery.demo. Out of M1 OpenAPI scope.
Entities: Order, OrderItem


### payments (deferred post-M1)
Stripe PaymentIntents and webhooks; card data never on server. Checkout reserves stock; failed/expired payment releases it. Out of M1 OpenAPI scope.
Entities: Payment, Order


## Mobile app features
- catalog: screens ProductListScreen (/products) — scrollable jewellery cards with name, primary image or placeholder, formatted price from integer cents + USD (e.g. Tropical Earring as $19.99 from 1999 cents); client-side search (case-insensitive on name/searchable text) and filters for price range, category (earrings|necklaces|bracelets|rings), metal (gold-tone|silver-tone|rose-gold), occasion (everyday|work|gift|party); empty and error/retry states; ~12–20 seeded SKUs, ProductDetailScreen (/products/:id) — name, description, price (cents + USD), category, metal, occasion, stock/availability; aggregate star rating (1–5) and mock review list (rating + text) or empty-reviews state; Add to cart (≥48dp) for in-stock items; back preserves list search/filter state (state: CatalogRepository (M1: LocalCatalogDataSource from assets/data/catalog.json; M2+: generated CatalogApi). ProductListNotifier (AsyncNotifier) holds AsyncValue of products plus q, min/max priceCents, category, metal, occasion filters. ProductDetailNotifier loads one product by id including averageRating and reviews. Price formatting helpers convert cents → display string without floats.)
- cart: screens CartScreen (/cart) — line items with product name, unit price snapshot (cents + currency) copied at add time, quantity steppers (≥48dp), decrease to 0 removes line; line and cart totals recalculated with integer minor units only; empty on cold start (state: CartNotifier (Notifier<CartState>) session-only in-memory for M1; clears on full process restart. Add/increment from ProductDetailScreen for in-stock items. No persistence, auth, payment, or backend sync in M1.)
- core: screens  (state: Design tokens in lib/core/theme (agent-selectable; no style-approval gates); go_router routes /products, /products/:id, /cart; no live HTTP in M1 debug builds (offline mock). Debug Android cleartext only for 10.0.2.2 when backend arrives.)

## Data model
All monetary amounts are Int minor units (cents) with ISO 4217 currency code USD; never floats. Product is the merchandising parent (jewellery listing with category, MetalTone, Occasion, description, primary image); ProductVariant is the purchasable SKU with its own priceCents, currency, stockQuantity (and reservedQuantity for M2+ checkout holds). Listing cards show display price from the default or lowest active variant. Category slugs: earrings, necklaces, bracelets, rings. MetalTone: gold_tone, silver_tone, rose_gold. Occasion: everyday, work, gift, party. Flagship seed: Tropical Earring at 1999 cents USD displayed as $19.99. Review stores starRating (1–5) and body text; ProductDetail exposes averageRating and reviews[] (mock in M1; write path and verified-purchase deferred). CartItem and OrderItem snapshot productName and unitPriceCents at write time so later catalog edits do not alter past carts/orders. Order.status: pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Stock reservation at checkout (M2+); failed or expired payment releases reserved stock. User.passwordHash uses bcrypt or argon2; support account deletion with PII removal/anonymization. M1 runtime uses only embedded mock catalog JSON—no Prisma/Postgres connection.

## Security
- M1 ships no auth, no mandatory network calls, and no PII, passwords, or payment data—mock catalog is read-only embedded data; do not send catalog or cart data to external payment providers in this increment.
- M2+ JWT bearer auth: access tokens 15-minute TTL, refresh tokens rotated and stored hashed server-side; flutter_secure_storage on mobile.
- Passwords hashed with bcrypt (cost ≥12) or argon2id; never store plaintext.
- All API input validated via class-validator DTOs; responses match OpenAPI schemas exactly; errors return { statusCode, error, message }.
- Stripe webhook verifies Stripe-Signature; idempotent event handling; card PAN/CVC never touch Womens Jewellery servers.
- HTTPS-only in release mobile builds; debug Android allows cleartext to 10.0.2.2 only via network_security_config.
- Config and secrets via environment variables validated at NestJS startup (@nestjs/config)—never committed.
- Minimum personal data collection; account deletion removes or anonymizes PII.
- Catalog and health endpoints are public (security: []); bearerAuth scheme is declared for future protected modules.

## Architecture decisions
### ADR-001: Local embedded mock catalog for Womens Jewellery M1 Speed Demo
**Context:** PRD requires the smallest runnable Flutter MVP on an Android emulator immediately with ~12–20 jewellery SKUs, search/filters, product detail with mock reviews, and an in-memory cart. NestJS, Postgres, generated clients, and CI would delay the demo. US-001/US-002/US-003 need browse, detail, and session cart only—no auth, payments, or checkout. Backend work is explicitly deferred if it slows delivery.

**Decision:** M1 loads ~12–20 Womens Jewellery SKUs from assets (catalog.json + image assets), including Tropical Earring at 1999 cents USD. Search, filters (price, category, metal, occasion), stock display, and mock reviews run in-process. No HTTP client is required in M1 builds. CatalogRepository abstracts the data source so M2 can swap to the generated OpenAPI client without rewriting screens. Style tokens are chosen by the agent without stakeholder style approval.

**Consequences:** Positive—offline demo, zero backend dependency, fastest path to validating browse → detail → cart UX. Negative—cart is session-only and anonymous; no shared stock truth; M2 must migrate to API and keep server as source of truth for catalog, inventory, and reviews.

### ADR-002: Integer minor units for all money fields
**Context:** Floating-point money causes rounding errors in cart totals and Stripe amounts. Project rules forbid floats for prices. Demo must show $19.99 from 1999 cents exactly for Tropical Earring.

**Decision:** Store and transmit all prices as integer cents with currency code USD (ISO 4217). Flutter, NestJS, Prisma Int, and OpenAPI integer schemas agree. Formatting to display strings (e.g. $19.99) happens only in the presentation layer; cart line and cart totals use integer arithmetic only.

**Consequences:** Positive—exact arithmetic, Stripe-compatible amounts, consistent contract. Negative—UI must use format helpers; developers must never use double for money.

### ADR-003: Contract-first OpenAPI 3.1 capped to M1 catalog operations
**Context:** Mobile convention requires a dart-dio client generated from OpenAPI. Hard scope limits this run to at most four API operations. Cart is in-memory and needs no API. Auth, payments, and checkout are out of scope. M1 prefers zero live business API dependency. Reviews are display-only from mock data and ship embedded on product detail—no separate review write API in M1.

**Decision:** Freeze OpenAPI 3.1 with GET /health (infra, uncapped), GET /products (search, price range, category, metal, occasion, pagination), and GET /products/{productId} (detail with variants, averageRating, reviews). Bearer auth is declared for M2+ but unused by these public operations. NestJS will implement controllers to match; Flutter generates packages/api_client when the backend ships.

**Consequences:** Positive—parallel M2 catalog work without over-building; mock models mirror schemas; generated types reduce drift; no approval gates block coding. Negative—later milestones must extend the same OpenAPI carefully; M1 cannot exercise a live API until NestJS exists.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.