# Architecture

Lighting Retail UK MVP is delivered in two milestones for stakeholder demo: M1 — a client-ready Flutter 3.x Android app (API 26+) with guest shopping, cohesive design tokens (warm neutral surfaces, high-contrast charcoal text, amber accent for CTAs), six screens, 12–20 seeded lighting SKUs in local mock assets, product listing with search and multi-facet filters, product detail with variants, lighting specifications, star ratings and reviews, and a session-only in-memory cart with quantity updates; M2 — a NestJS /api/v1 slice with PostgreSQL 16 + Prisma, GET /health, and contract-first catalog OpenAPI (seven public catalog operations, twelve-operation cap respected with /health and /api/docs-json excluded), seed data mirroring M1 products, Dart dio client generation when analyze/tests pass, with automatic fallback to M1 mocks if the API is unreachable. Full MVP (post-demo) extends the same modules with JWT auth, server-side carts for signed-in users, UK checkout with 20% VAT and flat shipping, Stripe PaymentIntents (test mode), webhooks, order history, coupons, wishlists, and admin catalog/order APIs—all modeled in Prisma now so later work does not reshape fundamentals. All prices are integer pence (minor units) with ISO 4217 GBP; stock is tracked per ProductVariant with reservation at checkout in production; order lines snapshot merchandising text and unit price at purchase time.

## Components
- **Flutter Mobile App (M1 primary, M2 API-aware)** (Flutter 3.x, Dart, Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, dio (M2+ via OpenAPI client), flutter_secure_storage (full MVP auth), flutter_test, integration_test): Guest shopper journey: home/category entry, searchable and filterable product listing, product detail with variant selection and lighting specs, ratings/reviews display, in-memory cart. M1 uses LocalCatalogDataSource (assets/data/catalog.json + bundled images). M2 toggles CatalogRepository to generated packages/api_client (dart-dio) when integration passes; on network failure falls back to mocks for demo resilience. Riverpod notifiers per feature; go_router with six routes; loading/empty/error on every screen; prices formatted from integer pence without floats; 48dp touch targets and semantic labels on imagery.
- **Local Mock Catalog (M1)** (assets/data/catalog.json, assets/images/products/*, Dart freezed models): Source of truth for demo when API is off or unreachable. Seeds 12–20 parent products across the fixed UK lighting taxonomy with 15–30 purchasable variants total, GBP pence prices, brands, SKUs, wattage/lumen/color-temp/IP specs, popularityRank and unitsSold90Days for sort, seeded reviews and aggregate ratings. JSON shape matches OpenAPI ProductSummary, ProductDetail, LightingSpecs, and Review schemas for drop-in M2 swap.
- **NestJS API Server (M2)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Jest, Supertest): Contract-first REST under /api/v1. Modules: health, catalog (categories, products, reviews, facets, home). Thin controllers, catalog services, PrismaService for PostgreSQL. class-validator DTOs; @nestjs/swagger serves /api/docs-json. Jest unit tests per service; Supertest e2e per controller. Config validated at startup via @nestjs/config.
- **PostgreSQL Database** (PostgreSQL 16, Prisma ORM): System of record for catalog seed (M2), and full MVP domains (users, carts, orders, payments, coupons, wishlists, analytics events). ACID transactions for stock reservation/release and order creation.
- **Stripe Payments (full MVP)** (Stripe API, stripe-node, Stripe Flutter SDK, signed webhooks): PaymentIntents in test mode: server creates intent, Flutter confirms via Stripe SDK, webhook marks order paid. Card data never touches NestJS except Stripe tokens/IDs.
- **Docker / CI** (Docker, docker-compose, GitHub Actions): docker-compose for API + Postgres staging; GitHub Actions runs lint, Jest, Supertest, and Flutter analyze/test on PRs.

## Backend modules
### health
Liveness and database connectivity for staging and M2 demo. Does not count toward the twelve-operation cap.
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only lighting catalog for M2 US-001–US-004 and US-006: home merchandising, category tree, faceted product list (search, filter, sort), product detail with variants and lighting specifications, paginated reviews. Seed data must match M1 mock SKUs and core fields.
Entities: Category, Product, ProductVariant, LightingSpecification, ProductImage, Review, Brand

- `GET /api/v1/home`
- `GET /api/v1/categories`
- `GET /api/v1/categories/{slug}`
- `GET /api/v1/catalog/facets`
- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`
- `GET /api/v1/products/{productId}/reviews`

### auth
Email/password register, login, logout, refresh, password reset, account deletion (full MVP). JWT access 15 min + refresh rotation. Not implemented in M2 demo slice; bearerAuth declared in OpenAPI for future operations.
Entities: User, RefreshToken, PasswordResetToken


### users
Profile and UK shipping addresses for registered customers (full MVP).
Entities: User, Address


### cart
Persisted cart per signed-in user (full MVP). M1/M2 demo uses client in-memory cart only (US-005); no cart API in this run's OpenAPI.
Entities: Cart, CartItem


### orders
Checkout, order placement, guest lookup by order number + email, order history, status lifecycle pending_payment → paid → fulfilled → delivered plus cancelled/refunded (full MVP). OrderItem snapshots name and unit price.
Entities: Order, OrderItem, StockReservation


### payments
Stripe PaymentIntent creation, webhook handling, idempotent paid transition, stock reservation coupling (full MVP).
Entities: Payment, Order


## Mobile app features
- home: screens HomeScreen (/) — category grid for top-level taxonomy (Ceiling, Wall, Outdoor & Security, Bulbs & Tubes, LED Strips, Lamps & Portable, Commercial & Trade), featured product carousel, quick search entry; loading/empty/error states (state: HomeNotifier (AsyncNotifier): M1 loads categories + featured from mock; M2 calls getHome via CatalogRepository. Search query forwarded to ProductListingScreen via go_router query params.)
- catalog: screens ProductListingScreen (/products) — scrollable product cards (image, name, brand, formatted GBP price from pence, Out of stock badge), inline search field, filter/sort sheet, category context from route; supports US-001–US-003, ProductDetailScreen (/products/:productId) — gallery, variant chips (finish/wattage/CCT), price/SKU/stock per variant, lighting specifications section (only non-null spec fields), ratings summary, preview of reviews with link to full list, add-to-cart (disabled when OOS); US-004, ProductReviewsScreen (/products/:productId/reviews) — paginated review list and aggregate stars; US-004 (state: CatalogRepository abstraction (LocalCatalogDataSource | ApiCatalogDataSource). ProductListNotifier holds filter state (brandSlugs, categorySlug, price range pence, wattage, finish, inStockOnly, sort). ProductDetailNotifier loads detail by id and tracks selectedVariantId. ReviewsNotifier paginates listProductReviews.)
- cart: screens CartScreen (/cart) — line items with product name, variant label, unit price snapshot (pence GBP), quantity steppers, remove, subtotal; empty state; US-005 (state: CartNotifier (Notifier<CartState>) session-only in-memory Map keyed by variantId; snapshots productName, variantLabel, unitPriceCents, currency at add time; no persistence or API in demo run.)
- core: screens AppShell — bottom navigation or rail linking Home, Products, Cart within six-screen budget; consolidates filter UI as modal bottom sheet on ProductListingScreen (not a separate route) (state: lib/core/theme design tokens (colors, spacing, typography); lib/core/network ApiConfig (baseUrl http://10.0.2.2:3000/api/v1 debug); go_router routes; debug android/app/src/debug network_security_config cleartext for 10.0.2.2 only; release https-only.)

## Data model
Monetary amounts are Int minor units (pence) with currency GBP (ISO 4217) everywhere—OpenAPI, Prisma, Dart, and PostgreSQL; never floats. Product is the merchandising parent; ProductVariant is the purchasable SKU with sku, priceCents, stockQuantity, reservedQuantity (checkout holds), and variant attributes (finish, wattageW, colorTemperatureK). Listing price uses default variant or lowest in-stock active variant; compareAtPriceCents optional for sale display. Category supports parentId for subcategories (e.g. Ceiling Lights → Pendant). LightingSpecification is 1:1 with Product with nullable columns for wattage, lumens, colorTemperatureK, lightType, voltage, dimmable, material, finish, dimensionsMm, ipRating, bulbIncluded, installationType—detail UI shows only populated fields. Review rows seed demo content; aggregate averageRating and reviewCount denormalized on Product for list performance. Popularity sort: popularityRank ASC NULLS LAST, then unitsSold90Days DESC; product view analytics stored but do not affect sort in MVP. CartItem and OrderItem snapshot productName, variantLabel, sku, unitPriceCents at write time. Order.status enum pending_payment, paid, fulfilled, delivered, cancelled, refunded. StockReservation ties variantId to orderId with expiresAt; payment failure/expiry releases reservedQuantity back to available stock. User.passwordHash bcrypt or argon2id; role CUSTOMER | ADMIN. Guest checkout (full MVP) uses guestEmail on Order with nullable userId. Coupons: one per order, constraints in Coupon model (not exposed in this OpenAPI). WishlistItem for registered users post-demo. All mutable Prisma models include createdAt and updatedAt for audit consistency.

## Security
- M1: no auth, no PII collection, embedded read-only catalog; cart is volatile memory only.
- M2 catalog and health endpoints are public (security: []); HTTPS in release; debug cleartext limited to 10.0.2.2 via Android network security config.
- Full MVP: JWT bearer access tokens (15-minute TTL) and refresh token rotation stored hashed server-side; flutter_secure_storage for access/refresh on mobile.
- Passwords hashed with bcrypt (cost ≥12) or argon2id; account deletion soft-deletes/anonymizes PII per GDPR-minded minimum retention.
- Input validation via class-validator DTOs; errors always { statusCode, error, message } with correct HTTP status.
- Stripe webhook verifies Stripe-Signature; idempotent processing by stripeEventId; no raw card PAN/CVC on server.
- Admin role gates future mutating catalog/order routes; single ADMIN role for MVP.
- Secrets and DATABASE_URL via environment variables validated at NestJS startup; never committed.
- Rate limiting on auth and checkout endpoints (full MVP hardening); catalog reads unauthenticated but cacheable.

## Architecture decisions
### ADR-001: Dual-path catalog: M1 local mock with M2 OpenAPI repository swap
**Context:** PRD requires a showable Android demo without blocking on backend integration, while M2 must prove contract alignment via NestJS and a generated Dart client. Stakeholder demo must not fail if API or codegen is unavailable.

**Decision:** Introduce CatalogRepository with LocalCatalogDataSource (assets) and ApiCatalogDataSource (generated client). Feature flag or runtime probe selects API when health succeeds and codegen tests pass; otherwise M1 mock path. OpenAPI schemas are the single contract; mock JSON conforms exactly.

**Consequences:** Positive: reliable demo, parallel frontend/backend work, reduced drift when models match OpenAPI. Negative: two sources to update when seed changes—mitigated by one seed script writing both JSON export and Prisma seed.

### ADR-002: Integer pence and GBP as the only money representation
**Context:** UK retail with 20% VAT and Stripe requires exact minor-unit arithmetic; project rules forbid floating-point money.

**Decision:** Store and transmit priceCents (and all totals) as integers with currency GBP in API, Prisma, and Flutter domain models. Presentation layer formats en-GB currency strings; VAT/shipping calculations use integer math with explicit rounding policy (half-up to penny on display only).

**Consequences:** Positive: Stripe-compatible amounts, consistent contracts, no binary rounding bugs. Negative: developers must not use double for money; filter price ranges use pence integers in API query params.

### ADR-003: Contract-first OpenAPI 3.1 with seven catalog operations for M2
**Context:** Hard cap of twelve API operations excludes infrastructure /health and /api/docs-json. Must-have stories US-001–US-006 need browse, search, filter, sort, detail, specs, reviews, and health—not auth, cart, or checkout yet.

**Decision:** Publish OpenAPI 3.1 with operationIds for getHealth, getHome, listCategories, getCategoryBySlug, getCatalogFacets, listProducts, getProductById, listProductReviews. NestJS implements controllers to match schemas exactly; Flutter generates packages/api_client when analyze/tests pass. bearerAuth declared but unused by these operations.

**Consequences:** Positive: codegen-friendly client, explicit PM/work breakdown per operation, room under cap for later auth/checkout extensions. Negative: home and facets add endpoints beyond minimal CRUD—justified by demo UX and filter UX needs.

### ADR-004: Stock and reservations at variant granularity
**Context:** Lighting SKUs differ by wattage, finish, and color temperature; overselling must be prevented at checkout in full MVP while demo shows per-variant availability on detail and listing badges.

**Decision:** StockQuantity and reservedQuantity live on ProductVariant. Checkout creates StockReservation rows and increments reservedQuantity; payment success converts reservation to deduction; failure/expiry releases reservation. Listing inStock is true if any active variant has available stock (stockQuantity - reservedQuantity > 0).

**Consequences:** Positive: aligns with e-commerce domain rules and trade buyer quoting. Negative: cart and listing must reference variantId, not productId alone; add-to-cart disabled when selected variant OOS.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.