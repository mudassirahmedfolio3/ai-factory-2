# Architecture

Milestone 1 (Browse MVP) is an Android-first Flutter 3.x speed demo: a local/mock product catalog drives Product List and Product Detail, with an optional in-memory Cart screen. No sign-in, payments, checkout, or live NestJS backend are required to run on an emulator. Prices are integer minor units (cents) with ISO 4217 USD; stock is per ProductVariant. The OpenAPI 3.1 contract and Prisma schema define the catalog shape the mock data mirrors and that a later NestJS/PostgreSQL backend will implement (at most four business API operations plus health). Auth, Stripe, orders, and persisted carts are deferred.

## Components
- **Flutter Mobile App (Android)** (Flutter 3.x, Dart, Riverpod, go_router, flutter_secure_storage (unused in M1), design tokens in lib/core/theme): Deliver the M1 browse journey: load mock catalog, show product list and detail (name, photos, description, variants, availability, USD cents), and maintain an optional process-lifetime in-memory cart. No network dependency for M1 demo.
- **Local Mock Catalog** (Dart fixtures / JSON assets under features/catalog/data): Ship static/fixture product and variant data inside the app so list/detail render immediately without a backend. Same fields as OpenAPI Product/ProductVariant schemas (cents, USD, per-variant stock).
- **In-Memory Cart Store** (Riverpod Notifier in features/cart): Hold CartItems for the current process only: product name, variant identity/label, quantity, unitPriceCents and currency copied at add time; line totals via integer arithmetic. Cleared on process restart.
- **API Contract (forward-looking)** (OpenAPI 3.1 YAML; future packages/api_client (dart-dio)): Document catalog list/detail and health so dart-dio client generation stays aligned; M1 app may ignore generated client and read mock data. Max four business operations.
- **Backend (deferred past M1 runtime)** (NestJS, Prisma, PostgreSQL 16, Docker (later milestones)): Later NestJS services implement the same catalog contract against PostgreSQL via Prisma. Not blocking the M1 Flutter demo.

## Backend modules
### health
Liveness/readiness: return 200 when the database is reachable (staging/prod). Documented for later NestJS; not required for M1 Flutter mock demo.
Entities: 

- `GET /api/v1/health`

### catalog
Read-only product catalog: paginated product list and product detail including variants and per-variant stock. Public (no JWT required). M1 Flutter uses mock data shaped identically; NestJS/Prisma implement these endpoints in a later milestone.
Entities: Category, Product, ProductVariant

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`
- `GET /api/v1/categories`

## Mobile app features
- catalog: screens ProductListScreen, ProductDetailScreen (state: Riverpod AsyncNotifier loads mock catalog (list) and selected product+variants (detail). Handles loading, empty, and error. Navigation via go_router routes /products and /products/:productId.)
- cart: screens CartScreen (state: Riverpod Notifier holds in-memory CartState (items with name, variantLabel, quantity, unitPriceCents, currencyCode USD). Add from ProductDetailScreen; lineTotalCents = unitPriceCents * quantity using integer math. Not persisted. Route /cart.)
- core: screens  (state: Shared theme tokens (lib/core/theme), go_router shell, and optional Dio/api_client stub for later milestones. M1 browse path does not call a live API.)

## Data model
M1 runtime data is local/mock only. Canonical money fields: unitPriceCents (Int) + currencyCode (ISO 4217, always USD in M1). Stock lives on ProductVariant.stockQuantity (Int >= 0); list/detail show availability from selected variant. Cart lines copy productName, variantLabel, unitPriceCents, currencyCode at add time so later catalog edits cannot change bag lines. Category is optional grouping for list filters later; M1 may show a flat list. User, Address, Order, OrderItem, Payment, and server-side Cart are modeled in Prisma for later milestones but unused in M1. Order status enum reserved: pending_payment, paid, fulfilled, delivered, cancelled, refunded. No floating-point money anywhere.

## Security
- M1 collects no PII, passwords, or card data; no auth or Stripe SDKs in the app for this milestone.
- Catalog read APIs are public (no bearer required). JWT bearer scheme is declared in OpenAPI for later authenticated modules; access 15m / refresh tokens when auth lands.
- Android debug may allow cleartext only to 10.0.2.2 for local staging; release builds HTTPS-only. M1 mock path uses neither.
- Passwords (later) hashed with bcrypt or argon2; store minimum personal data; support account deletion when accounts exist.
- Card data never touches our servers (Stripe PaymentIntents + webhook) in later milestones; not in M1.
- Generated API client and NestJS must not log secrets; config via env vars validated at startup.

## Architecture decisions
### ADR-001: Local mock catalog for M1 instead of live NestJS API
**Context:** M1 must run on an Android emulator immediately after build/install. Building NestJS, Prisma, PostgreSQL, and Docker before browse UI would block the speed demo.

**Decision:** Ship product/variant fixtures inside the Flutter app. Product List and Product Detail read only from that mock. OpenAPI + Prisma still define the contract and DB model for the next milestone, but NestJS implementation is out of M1 delivery.

**Consequences:** Demo has zero network dependency and meets US-001/US-002 quickly. Mock and OpenAPI schemas must stay field-aligned. Switching to generated API client later is a focused catalog data-layer swap.

### ADR-002: In-memory cart only; no cart or checkout APIs in M1
**Context:** US-003 needs a multi-item bag preview. Project conventions normally use signed-in server carts and Stripe checkout, which are out of scope for M1.

**Decision:** Implement CartScreen with a Riverpod in-memory store. Lines copy name, variant, quantity, and unitPriceCents (USD) at add time. No persistence, no checkout, no cart REST operations in the M1 OpenAPI operation budget.

**Consequences:** Cart empties on process restart (accepted). Integer cents math avoids float bugs. Later milestones replace this with authenticated Cart APIs and stock reservation without changing browse UX.

### ADR-003: Contract-first catalog OpenAPI with public GETs and cents/USD
**Context:** Developers need an exact API and money model even while M1 uses mocks. Scope allows at most four API operations plus health.

**Decision:** Publish OpenAPI 3.1 with GET /api/v1/health, GET /api/v1/categories, GET /api/v1/products (page, pageSize → items, total), and GET /api/v1/products/{productId}. Prices are integer cents + currencyCode. Bearer auth is documented globally but catalog/health operations set security: []. Error body is {statusCode, error, message}.

**Consequences:** operationIds drive dart-dio generation later. Pagination and error shapes match NestJS conventions. Auth/payments/orders stay out of the M1 contract surface.

### ADR-004: Prisma models catalog now; commerce entities stubbed for later
**Context:** Full domain includes User, Cart, Order, Payment, but M1 must not block on backend work. PM still needs an explicit data model.

**Decision:** Prisma schema includes Category, Product, ProductVariant as first-class M1-aligned tables, plus User/Address/Cart/CartItem/Order/OrderItem/Payment models for subsequent milestones without exposing those APIs in M1.

**Consequences:** Single schema evolves with migrations later. M1 Flutter fixtures mirror Product/ProductVariant columns. No M1 requirement to run Postgres for the demo.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.