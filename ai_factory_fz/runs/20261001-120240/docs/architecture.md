# Architecture

ShirtStack M1 (Speed Demo) delivers a Flutter 3.x Android-first mobile app that browses a locally embedded mock catalog of 20–40 men's shirt SKUs and shows product detail, with an optional in-memory cart that clears on app restart. No backend, auth, payments, or checkout ship in M1—the app must launch offline on an emulator within one sprint. This document defines the production-ready target architecture (NestJS + PostgreSQL + Stripe) so M2+ developers can implement against a frozen contract without guessing, while explicitly scoping M1 mobile work to mock data only. Prices are integer USD cents everywhere; stock, orders, and signed-in carts arrive in later milestones. M1 OpenAPI contract is limited to health plus two catalog read operations (US-001/US-002).

## Components
- **Flutter Mobile App (M1 primary)** (Flutter 3.x, Dart, Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, flutter_secure_storage (M2+), integration_test): Renders product list (browse), product detail, and optional in-memory cart. Embeds seeded mock catalog JSON/assets for M1. Handles loading, empty, and error states; filters and search run client-side against local data. Post-M1, switches to generated OpenAPI client (dart-dio) against NestJS.
- **Local Mock Catalog (M1)** (assets/data/catalog.json, bundled image assets, Dart freezed models): Provides 20–40 men's shirt SKUs with title, priceCents, currency USD, primary image, sizes, colors, fit type, shirt type, description, and variants. Source of truth for M1 browse/detail; shapes mirror OpenAPI ProductSummary/ProductDetail for easy M2 swap.
- **NestJS API Server (M2+)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Jest, Supertest): Contract-first REST API at /api/v1. Thin controllers, service-layer business logic, Prisma data access. Catalog read endpoints for browse/detail first; auth, cart, orders, payments modules added incrementally after M1.
- **PostgreSQL Database (M2+)** (PostgreSQL 16, Prisma ORM): System of record for users, catalog, carts, orders, payments metadata, reviews, promo codes. ACID transactions for stock reservation and order creation.
- **Stripe (M2+)** (Stripe API, Stripe SDK (Flutter), webhook signing secret): PaymentIntents (test mode), webhook confirmation of paid orders, Stripe Tax for US sales tax. Card data never touches ShirtStack servers.
- **Docker / CI (M2+)** (Docker, docker-compose, GitHub Actions): docker-compose for local/staging (API + Postgres). GitHub Actions runs lint, unit, and e2e tests on PR.

## Backend modules
### health
Liveness and database connectivity probe. Included in M1 OpenAPI contract; NestJS implementation deferred until backend work starts (does not block Flutter M1).
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only product catalog for browse and detail. Supports pagination, text search, and filters (size, color, shirt type, price range). Product detail includes variants with per-variant price and stock (stock enforced M2+). M1 Flutter uses local mock shaped like these responses; NestJS implements these two operations first in M2.
Entities: Category, Product, ProductVariant

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`

### auth (deferred post-M1)
Email/password registration and login, Google/Apple OAuth, JWT access (15 min) and refresh tokens, account deletion. Out of M1 OpenAPI scope.
Entities: User, RefreshToken


### users (deferred post-M1)
Profile and saved shipping addresses for checkout. Out of M1 OpenAPI scope.
Entities: User, Address


### cart (deferred post-M1)
Signed-in user cart persisted server-side. M1 uses in-memory CartNotifier only; guest carts remain out of scope. Out of M1 OpenAPI scope.
Entities: Cart, CartItem


### orders (deferred post-M1)
Order placement and history with status lifecycle pending_payment → paid → fulfilled → delivered, plus cancelled/refunded. Order lines snapshot product name and unit price. Out of M1 OpenAPI scope.
Entities: Order, OrderItem


### payments (deferred post-M1)
Stripe PaymentIntents and webhooks; card data never on server. Out of M1 OpenAPI scope.
Entities: Payment, Order


## Mobile app features
- catalog: screens ProductListScreen (/products) — grid/list of shirts with title, formatted price, primary image, available sizes, color, fit type; client-side filter by size, color, price range, shirt type; real-time title/attribute search; empty state when no matches, ProductDetailScreen (/products/:id) — title, description, formatted USD price, primary image, size/color selectors, fit type, 30-day returns policy section, sticky add-to-cart bar (≥48dp touch target) (state: CatalogRepository (M1: reads LocalCatalogDataSource embedded JSON; M2+: CatalogApi via generated client). ProductListNotifier (AsyncNotifier) holds filter/search state and derived list. ProductDetailNotifier loads single product by id.)
- cart (optional M1): screens CartScreen (/cart) — line items with product name, unit price (cents, copied at add), size/color, quantity, subtotal; remove/decrement to zero removes line (state: CartNotifier (Notifier<CartState>) in-memory only for M1; clears on app restart. Add-to-cart from ProductDetailScreen with brief SnackBar confirmation. M2+ replaces with server-synced cart via API.)
- core: screens  (state: AppTheme from lib/core/theme design tokens; go_router routes for /products, /products/:id, /cart; no network client in M1 debug builds (offline-first mock).)

## Data model
All monetary amounts are Int (minor units, cents) with currency ISO 4217 code (USD only for launch). Product is the merchandising parent; ProductVariant is the purchasable SKU (size + color combination) with its own priceCents and stockQuantity. Listing cards aggregate distinct sizes/colors from active variants. OrderItem and CartItem snapshot productTitle and unitPriceCents at write time so catalog edits never alter history. Order.status enum follows pending_payment → paid → fulfilled → delivered, plus cancelled and refunded. Stock reservation occurs at checkout (M2+); failed/expired PaymentIntent releases reserved stock. User.passwordHash uses bcrypt or argon2; support soft-delete or anonymization for account deletion. M1 Flutter app uses a static List<Product> + variants in assets/data/catalog.json—no Prisma/Postgres at runtime. Category is fixed to men's shirts for MVP but modeled for future expansion. Reviews and PromoCode tables exist in Prisma for full release but have zero M1 API operations.

## Security
- M1 ships no auth, no network calls, no PII collection—mock catalog is read-only embedded data.
- M2+ JWT bearer auth: access tokens 15-minute TTL, refresh tokens rotated and stored hashed server-side; flutter_secure_storage on mobile.
- Passwords hashed with bcrypt (cost factor ≥12) or argon2id; never store plaintext.
- All API input validated via class-validator DTOs; responses match OpenAPI schemas exactly.
- Stripe webhook endpoint verifies Stripe-Signature header; idempotent processing of payment events.
- Card PAN/CVC never touch ShirtStack servers—Stripe SDK on device confirms PaymentIntent.
- HTTPS-only in release mobile builds; debug Android allows cleartext to 10.0.2.2:<port> only via network_security_config.
- Rate limiting on auth endpoints (M2+); CORS restricted to known origins.
- Account deletion removes or anonymizes PII per GDPR-style minimum-data principle.
- PostgreSQL credentials and Stripe secrets via environment variables validated at startup (@nestjs/config)—never committed.

## Architecture decisions
### ADR-001: Local embedded mock catalog for M1 Speed Demo
**Context:** PRD requires a demo-ready Flutter app on an emulator in one sprint with browse and detail screens. Building NestJS, Postgres, OpenAPI client generation, and CI would delay the investor demo.

**Decision:** M1 loads 20–40 shirt SKUs from embedded assets (catalog.json + bundled images). All filtering and search run in-process. No HTTP client invoked in M1 builds. Repository interface abstracts data source so M2 swaps to generated API client without UI rewrites.

**Consequences:** Positive—zero backend dependency, offline demo, fastest path to screen validation. Negative—cart is in-memory only; no stock truth; team must migrate to API client in M2 and avoid duplicating business rules long-term (server becomes source of truth for filters/validation).

### ADR-002: Integer minor units for all money fields
**Context:** Floating-point arithmetic causes rounding errors in e-commerce totals, tax, and Stripe amounts.

**Decision:** Store and transmit all prices as integer cents (e.g., 2799 = $27.99) with currency code "USD". Flutter and NestJS use int; Prisma Int; OpenAPI integer format. Display formatting happens only in presentation layer.

**Consequences:** Positive—exact ledger math, Stripe-compatible amounts, consistent API contract. Negative—developers must never use double for money; format helpers required in UI.

### ADR-003: Contract-first OpenAPI 3.1 limited to M1 catalog operations
**Context:** Mobile convention mandates dio client generated from OpenAPI; hard scope caps this run at four API operations and must-have stories US-001/US-002 (browse + detail). Cart is in-memory and needs no API in M1.

**Decision:** Freeze OpenAPI 3.1 now with GET /health (infra), GET /products, and GET /products/{productId} only. Bearer auth scheme is declared for M2+ clients. NestJS implements these controllers to match the spec; Flutter generates packages/api_client when backend is ready. Auth, cart, orders, and payments stay out of this document's paths.

**Consequences:** Positive—parallel M2 catalog work without over-building; generated types reduce drift; mock models mirror ProductSummary/ProductDetail. Negative—later milestones must extend the same OpenAPI file carefully; M1 cannot exercise live API until NestJS ships.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.