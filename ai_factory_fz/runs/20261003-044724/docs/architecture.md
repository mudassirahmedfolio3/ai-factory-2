# Architecture

ShopEase Release 2 (M3 — shopper depth) extends the existing M1 Flutter catalog and M2 NestJS catalog API with authenticated commerce: JWT auth, API-backed cart and wishlist with guest-local counterparts and merge/import on login, merchandised home, enriched product discovery (search, sort, brand and availability filters), US-only checkout with flat shipping, fixed-percent tax, single coupon, mock server-side payment (no Stripe), order history with shopper-facing status labels and shipment tracking, mock password reset, and simulated support. The global API prefix is /api/v1. Contract-first OpenAPI 3.1 is the source of truth; PostgreSQL 16 via Prisma stores all server state. Exactly 24 counted API operations (excluding GET /health and OpenAPI JSON). Twelve new work items WI-010–WI-021. Money is integer USD cents everywhere on the wire and in the database.

## Components
- **Flutter ShopEase App (Android-first)** (Flutter 3.x, Dart, Riverpod, go_router, dio, freezed/json_serializable, integration_test): Shopper UI: home merchandising, catalog discovery, guest and signed-in cart/wishlist, checkout, mock payment, orders, auth, support and legal placeholders. Uses generated OpenAPI client (dart-dio), Riverpod, go_router, flutter_secure_storage for tokens.
- **NestJS API Server** (NestJS (TypeScript), class-validator DTOs, @nestjs/swagger, Jest, Supertest): HTTP API implementing OpenAPI contract: auth, catalog/home, cart, wishlist, checkout quotes, orders, mock payments with stock reservation, coupons, users, support stub. Thin controllers, domain services, PrismaService for persistence.
- **PostgreSQL Database** (PostgreSQL 16, Prisma ORM): System of record for users, catalog, carts, wishlists, coupons, orders, payments (mock), inventory reservations, password-reset tokens, support messages, home merchandising.
- **Docker Compose Staging** (Docker, docker-compose, GitHub Actions): Local/staging stack: API + Postgres for emulator (10.0.2.2) and CI e2e.
- **OpenAPI Contract & Generated Dart Client** (OpenAPI 3.1 YAML, openapi-generator (dart-dio)): Single contract drives NestJS Swagger validation and packages/api_client code generation; prevents hand-written endpoints in mobile.

## Backend modules
### HealthModule
Liveness and database connectivity probe for deploy and emulator smoke tests.
Entities: 

- `GET /api/v1/health`

### AuthModule
Register, login, logout, refresh tokens, mock forgot/reset password. Passwords hashed with bcrypt or argon2; refresh tokens stored hashed.
Entities: User, RefreshToken, PasswordResetToken

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`

### UsersModule
Account self-service: profile read optional in app; account deletion (soft-delete user, revoke tokens, anonymize where required).
Entities: User

- `DELETE /api/v1/users/me`

### CatalogModule
M2 baseline product list/detail extended with brand and availability filters, sort, search; category list for navigation.
Entities: Category, Product, ProductVariant

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`
- `GET /api/v1/categories`

### HomeModule
Merchandised home payload: banners, featured and new-arrival product summaries, category entry points.
Entities: HomeBanner, Product

- `GET /api/v1/home`

### CartModule
Signed-in user cart CRUD via replace semantics; merge guest cart on login (combine quantities per variant; fallback replace account cart with guest cart if merge fails). Prices snapshotted on cart lines from current variant price.
Entities: Cart, CartItem

- `GET /api/v1/cart`
- `PUT /api/v1/cart`
- `POST /api/v1/cart/merge`

### WishlistModule
Signed-in wishlist; one-time import merges local guest favorites without duplicate variants.
Entities: Wishlist, WishlistItem

- `GET /api/v1/wishlist`
- `PUT /api/v1/wishlist`
- `POST /api/v1/wishlist/import`

### CheckoutModule
Pre-order quote: validates US address fields, applies single coupon, computes subtotal/discount/shipping/tax/total in integer cents using seeded StoreConfig (free shipping threshold 7500 cents, flat rate 599 cents, tax 8% on taxable subtotal after discount).
Entities: Coupon, StoreConfig

- `POST /api/v1/checkout/quote`

### OrdersModule
Create order in pending_payment with line snapshots and stock reservation; mock payment marks paid; cancel/abandon releases reservation. List/detail for signed-in user with shopper status labels and shipment fields.
Entities: Order, OrderItem, ProductVariant

- `POST /api/v1/orders`
- `POST /api/v1/orders/{orderId}/complete-mock-payment`
- `POST /api/v1/orders/{orderId}/cancel`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{orderId}`

### PaymentsModule
Internal mock payment record linked to order; no external processor calls in Release 2. Invoked from OrdersModule complete-mock-payment.
Entities: Payment


### SupportModule
Persist support form submissions and return simulated-send confirmation (no outbound email in R2).
Entities: SupportMessage

- `POST /api/v1/support/messages`

## Mobile app features
- auth: screens AuthScreen (login + register tabs), ForgotPasswordScreen, ResetPasswordScreen (state: AuthNotifier (AsyncNotifier): register/login/logout; TokenStorage via flutter_secure_storage; AuthInterceptor on Dio client; redirect guests from order history via go_router)
- home: screens HomeScreen (state: HomeNotifier fetches GET /home; sections for banners, featured, new arrivals, categories; navigation to ProductDetailScreen or SearchResultsScreen with category filter)
- catalog: screens SearchResultsScreen (search, sort, filters — extends M1 list), ProductDetailScreen (M1 baseline + availability UX) (state: ProductListNotifier with query params; ProductDetailNotifier; shared CatalogRepository from api_client)
- cart: screens CartScreen (state: CartNotifier: GuestCartLocalRepository (shared_preferences/hive) vs ApiCartRepository when signed in; on login calls mergeCart then clears local; loading/empty/error states)
- wishlist: screens WishlistScreen (state: WishlistNotifier: local store for guests; API sync when authenticated; one-time import dialog on login/register)
- checkout: screens CheckoutScreen (address + review + coupon stepper) (state: CheckoutNotifier calls checkout/quote on address/coupon changes; validates US fields client-side; displays Money from integer cents)
- payment: screens MockPaymentScreen, OrderConfirmationScreen (state: PaymentNotifier: POST orders then POST complete-mock-payment; handles cancel path calling order cancel; confirmation shows orderNumber)
- orders: screens OrderHistoryScreen, OrderDetailScreen (state: OrdersNotifier paginated list; OrderDetailNotifier with shopperStatusStepper mapping paid/fulfilled→processing, fulfilled+tracking→shipped, delivered→delivered)
- account: screens AccountScreen (hub: orders, wishlist, support, legal, logout, delete account) (state: Derived auth state; links only; DeleteAccountNotifier calls DELETE /users/me)
- support: screens SupportScreen (state: SupportNotifier submits POST /support/messages; success confirmation UI)
- legal: screens LegalDocumentScreen (Privacy Policy and Terms of Sale placeholders via route query type) (state: Static content from lib/core/legal; no API)

## Data model
ProductVariant tracks stockQuantity and reservedQuantity; available = stockQuantity - reservedQuantity. Checkout create order increments reservedQuantity; mock pay decrements stockQuantity and reservedQuantity; cancel/failed pay decrements reservedQuantity only. CartItem and OrderItem store productName, variantName, unitPriceCents, currency at write time. Order includes human-readable orderNumber (unique), discountCents, optional couponCode, shipping/tax/total cents, shippingAddressSnapshot JSON for immutability, carrierName and trackingNumber populated when demo fulfillment marks shipped. Coupon supports PERCENT or FIXED_AMOUNT, minSubtotalCents, expiresAt, maxRedemptions optional, exclusions via CouponExclusion (category or product). WishlistItem unique per user+variant. User soft-delete via deletedAt; login rejected when deleted. PasswordResetToken single-use mock flow; forgot-password always returns 200 for unknown emails. HomeBanner ordered by sortOrder. Product.isFeatured and Product.isNewArrival drive home sections. Availability for filters: OUT_OF_STOCK when available<=0, LOW_STOCK when 0<available<=lowStockThreshold (seed default 5), IN_STOCK otherwise — exposed on ProductSummary as availability enum. Payment.provider=MOCK for Release 2; stripe fields nullable for future. StoreConfig singleton row seeded with shipping and tax rates.

## Security
- JWT access tokens (~15 min) and refresh tokens (~7 days); refresh stored server-side as hash; logout revokes refresh token.
- Passwords hashed with bcrypt (cost 12) or argon2id; never logged or returned.
- Bearer auth on all cart, wishlist, checkout, orders, users, logout, refresh except public catalog/home/auth register/login/forgot-password.
- Account deletion: soft-delete user, revoke refresh tokens, clear PII fields where feasible, retain order snapshots for legal minimum.
- Rate-limit auth and support endpoints in staging; validate all DTOs with class-validator; config via @nestjs/config with Joi/class validation at startup.
- Mobile: tokens only in flutter_secure_storage; debug cleartext limited to 10.0.2.2; release HTTPS only.
- Mock payment: no card data, no Stripe keys; complete-mock-payment idempotent per order in pending_payment only.
- Errors: { statusCode, error, message } with correct HTTP status; no stack traces in production responses.

## Architecture decisions
### ADR-001: Mock demo payment instead of Stripe for Release 2
**Context:** PRD requires demo-safe checkout without processor keys, webhooks, or card collection. M2 schema anticipated Stripe PaymentIntents.

**Decision:** Release 2 uses POST /orders/{orderId}/complete-mock-payment to transition pending_payment→paid and create a Payment row with provider MOCK. Stock is reserved at order creation and committed on mock pay. Stripe integration remains a future ADR without changing order line snapshot rules.

**Consequences:** Positive: zero external payment dependency for pilots. Negative: payment flow must be swapped for real Stripe later; Payment table keeps optional stripe fields nullable.

### ADR-002: Guest cart local-only with explicit server merge on login
**Context:** Guests shop without accounts; signed-in users need API persistence; US-003 requires merge with quantity combine and documented guest-wins fallback.

**Decision:** Guest cart and guest wishlist live in device local storage. On successful login/register, client calls POST /cart/merge with guest lines; server merges by variantId summing quantities capped by available stock. If merge fails, client may call PUT /cart with guest lines (replace). Wishlist uses POST /wishlist/import similarly.

**Consequences:** Positive: no guest session tracking on server; fits 24-op budget. Negative: cart not recoverable across devices until sign-in; merge edge cases must be QA-tested.

### ADR-003: Checkout quote endpoint for tax, shipping, and coupon validation
**Context:** Single coupon with complex rejection reasons; totals must be integer cents; client must show totals before order creation without duplicating business rules.

**Decision:** POST /checkout/quote accepts cart lines (or uses server cart for signed-in users), US shipping address, optional couponCode; returns full breakdown and couponValidation result. POST /orders uses same server-side calculator to prevent tampering.

**Consequences:** Positive: one source of truth for promo rules; clear error codes for UI. Negative: extra round trip before place order; server must keep quote logic in shared CheckoutPricingService.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.