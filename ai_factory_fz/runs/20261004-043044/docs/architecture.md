# Architecture

Lumen Lighting Retail UK Release 2 (M3) extends the M1 Flutter demo and M2 catalog API into an end-to-end UK B2C transactional slice branded Lumen. M3 delivers NestJS modules under /api/v1 for JWT auth (register, login, refresh, logout, password reset), profile and GDPR-minded account deletion, dual-mode cart (signed-in Cart persistence plus GuestCart keyed by X-Guest-Cart-Id with merge on login), UK checkout preview and order placement with integer pence totals, VAT-inclusive B2C GBP list prices, standard UK mainland shipping (flat rate; free over threshold), stock reservation at variant granularity, checkout idempotency via Idempotency-Key, mock secure payment (confirmMockPayment — no PAN/CVV collected; MockPaymentSession in Prisma), order history and detail for authenticated customers, and registered wishlist. Contract-first OpenAPI 3.1 (version 2.0.0-m3) defines twenty-eight counted operations; GET /health and GET /api/docs-json are infrastructure and excluded from the cap. Flutter M3 wires generated packages/api_client for catalog plus new auth, cart, checkout, payment, orders, and wishlist flows while retaining M1 mock fallback when the API is unreachable. Delivery is organized as work items WI-013 through WI-026 (backend modules, OpenAPI alignment, Prisma migrations/seed, NestJS e2e, Flutter screens and Riverpod notifiers, integration tests, staging demo). All money remains integer pence with ISO 4217 GBP; order lines snapshot merchandising at purchase time.

## Components
- **Flutter Mobile App (M1–M3 API-aware)** (Flutter 3.x, Dart, Riverpod, go_router, freezed/json_serializable, dio via OpenAPI-generated api_client, flutter_secure_storage): Shopper journey through home, faceted catalog, product detail with lighting specs and reviews, server-backed or guest cart, auth screens, checkout with address capture and delivery option, mock payment confirmation UI, order confirmation and history, wishlist for signed-in users. CatalogRepository switches between LocalCatalogDataSource and ApiCatalogDataSource; cart/auth/checkout use api_client with GuestCartId header persisted in flutter_secure_storage for guests and JWT for signed-in sessions. Riverpod notifiers per feature; go_router expanded routes; loading/empty/error on every screen; prices from integer pence.
- **Local Mock Catalog (M1 fallback)** (assets/data/catalog.json, Dart freezed models): Read-only catalog fallback when health check fails or codegen tests are skipped. Same ProductSummary/ProductDetail shapes as OpenAPI for resilient stakeholder demos.
- **NestJS API Server (M2 catalog + M3 commerce)** (NestJS (TypeScript), @nestjs/jwt, @nestjs/passport, Prisma, Jest, Supertest): Modules: health, catalog, auth, users, cart (guest + signed-in), checkout, payments (mock provider), orders, wishlist. class-validator DTOs; @nestjs/swagger; JWT guards with optional guest cart security []; PrismaService transactions for checkout, reservation, and payment state transitions.
- **PostgreSQL Database** (PostgreSQL 16, Prisma ORM): System of record for catalog, users, GuestCart/GuestCartItem, Cart/CartItem, orders, stock reservations, mock payment sessions, checkout idempotency, coupons (schema ready; validated at checkout preview), wishlists, home banners.
- **Mock Payment Provider (M3 Release 2)** (NestJS payments module, Prisma MockPaymentSession): Simulates payment capture without Stripe or card data. confirmMockPayment validates MockPaymentSession, marks Payment succeeded, transitions Order to paid, and finalizes stock reservations. Stripe fields remain nullable on Payment/Order for a later release.
- **Docker / CI** (Docker, docker-compose, GitHub Actions): docker-compose for API + Postgres; GitHub Actions runs lint, Jest, Supertest, Flutter analyze/test; OpenAPI drift checks against lumen_m3_openapi.yaml.

## Backend modules
### health
Liveness and database connectivity. Excluded from the twenty-eight-operation delivery cap.
Entities: 

- `GET /api/v1/health`

### catalog
Public read-only lighting catalog (seven operations): home with banners/new arrivals, categories, facets, product list/detail, reviews.
Entities: Category, Product, ProductVariant, LightingSpecification, ProductImage, Review, Brand, HomeBanner

- `GET /api/v1/home`
- `GET /api/v1/categories`
- `GET /api/v1/categories/{slug}`
- `GET /api/v1/catalog/facets`
- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`
- `GET /api/v1/products/{productId}/reviews`

### auth
Email/password registration and login, refresh rotation, logout, forgot/reset password. Issues JWT access (15 min) and refresh tokens hashed server-side.
Entities: User, RefreshToken, PasswordResetToken

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`

### users
Authenticated profile read and account deletion (soft-delete/anonymize PII).
Entities: User, Address

- `GET /api/v1/users/me`
- `DELETE /api/v1/users/me`

### cart
Guest cart via X-Guest-Cart-Id or signed-in Cart; add/update/remove lines with price snapshots; merge guest cart after login.
Entities: GuestCart, GuestCartItem, Cart, CartItem, ProductVariant

- `GET /api/v1/cart`
- `POST /api/v1/cart/items`
- `PATCH /api/v1/cart/items/{itemId}`
- `DELETE /api/v1/cart/items/{itemId}`
- `POST /api/v1/cart/merge`

### checkout
UK shipping preview and order creation with stock reservation, address snapshot JSON, coupon validation in preview, Idempotency-Key header.
Entities: Order, OrderItem, StockReservation, CheckoutIdempotency, Coupon, CouponCategory, CouponProduct

- `POST /api/v1/checkout/preview`
- `POST /api/v1/checkout/orders`

### payments
Mock payment confirmation for pending_payment orders; no card fields in API.
Entities: Payment, MockPaymentSession, Order

- `POST /api/v1/payments/mock/confirm`

### orders
Paginated order history and order detail for authenticated customers.
Entities: Order, OrderItem

- `GET /api/v1/orders`
- `GET /api/v1/orders/{orderId}`

### wishlist
Registered customer favorites by productId.
Entities: WishlistItem, Product

- `GET /api/v1/wishlist`
- `POST /api/v1/wishlist/items`
- `DELETE /api/v1/wishlist/items/{productId}`

## Mobile app features
- home: screens HomeScreen — categories, banners, featured and new-arrival carousels, search entry (state: HomeNotifier loads getHome via CatalogRepository; forwards search to ProductListingScreen.)
- catalog: screens CategoriesScreen — category and subcategory browse (US-001), ProductListingScreen — search, filters, sort, OOS badges, ProductDetailScreen — variants, specs, reviews preview, add-to-cart, ProductReviewsScreen — paginated reviews (state: CatalogRepository abstraction; ProductListNotifier, ProductDetailNotifier, ReviewsNotifier.)
- auth: screens LoginScreen, RegisterScreen, ForgotPasswordScreen, ResetPasswordScreen, AccountScreen — profile, logout, delete account (state: AuthNotifier holds session; secure storage for tokens; triggers cart merge on login.)
- cart: screens CartScreen — server lines, quantity steppers, guest vs signed-in indicator (state: CartNotifier calls getCart/add/update/remove; persists X-Guest-Cart-Id; mergeGuestCart after auth.)
- checkout: screens CheckoutScreen — UK address form, preview totals and coupon, MockPaymentScreen — secure mock payment outcome, OrderConfirmationScreen — order number and summary (state: CheckoutNotifier previewCheckout then createOrder with idempotency key; MockPaymentNotifier confirmMockPayment.)
- orders: screens OrderHistoryScreen, OrderDetailScreen — status timeline, line items, tracking when present (state: OrdersNotifier paginates listOrders; detail by orderId.)
- wishlist: screens WishlistScreen — add/remove from detail and list (state: WishlistNotifier; requires bearer token.)
- support: screens SupportScreen — UK contact, hours, FAQ WebView (static config, no API op) (state: Static support_content.dart; no Riverpod API dependency.)

## Data model
Monetary amounts are Int pence with currency GBP everywhere. GuestCart and GuestCartItem mirror CartItem snapshots for anonymous shoppers with TTL on GuestCart.expiresAt. Signed-in users have one Cart per userId. Checkout creates Order in pending_payment, StockReservation rows, and MockPaymentSession; confirmMockPayment consumes session and sets Payment.provider mock. CheckoutIdempotency stores Idempotency-Key to orderId for safe retries. Order.shippingAddressSnapshot is JSON for guest checkout; userId nullable with guestEmail. Payment.stripePaymentIntentId optional for future Stripe. CouponCategory/CouponProduct scope coupon eligibility; one coupon per order enforced in checkout preview. ProductVariant guestCartItems relation supports guest line integrity. Same variant-level stock and reservation rules as M1/M2 ADR-004. HomeBanner seeds getHome merchandising. Catalog seed targets 18–30 SKUs with imagery under app/assets/catalog/images and docs/IMAGE_SOURCES.md.

## Security
- Catalog and health remain public (security: []).
- Cart and checkout endpoints accept bearerAuth OR anonymous with X-Guest-Cart-Id (OpenAPI security: [bearerAuth, {}]).
- Wishlist and order history require JWT bearer access tokens (15-minute TTL) with refresh rotation stored hashed.
- Passwords hashed bcrypt or argon2id; deleteCurrentUser soft-deletes/anonymizes PII.
- Mock payment explicitly rejects PAN/CVV in schema; only orderId/session/outcome fields.
- Idempotency-Key required on createOrder to prevent duplicate orders on retry.
- HTTPS in release; debug cleartext limited to 10.0.2.2 for Android emulator.
- class-validator on all DTOs; uniform ErrorResponse shape.
- Rate limiting on auth and checkout in staging/production hardening.
- Secrets and configuration: all sensitive values (DATABASE_URL, JWT_ACCESS_SECRET, JWT_REFRESH_SECRET, optional STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET for future use) are supplied via environment variables or a secrets manager in staging/production; @nestjs/config validates required keys at startup with class-validator; no secrets committed to git or embedded in Flutter release builds; CI injects secrets from GitHub Actions encrypted secrets; local developers use .env (gitignored) and docker-compose env files; JWT signing keys rotated per environment; mobile stores only short-lived access tokens and refresh tokens in flutter_secure_storage, never database credentials.

## Architecture decisions
### ADR-001: Dual-path catalog: local mock with OpenAPI repository swap
**Context:** Demos must survive API outages; M2 proved contract alignment.

**Decision:** Retain CatalogRepository with local mock fallback while M3 adds live cart and checkout paths that require API when purchasing.

**Consequences:** Positive: resilient browse path. Negative: checkout cannot fully offline-demo without backend.

### ADR-002: Integer pence and GBP as the only money representation
**Context:** UK VAT and exact totals.

**Decision:** Unchanged from M1/M2 — all API and Prisma money fields are integer pence.

**Consequences:** Positive: no float rounding bugs. Negative: discipline required in UI formatting.

### ADR-003: OpenAPI 3.1 contract with twenty-eight counted operations for M3
**Context:** Release 2 adds auth, cart, checkout, mock payment, orders, wishlist under a raised cap while excluding infrastructure routes.

**Decision:** Publish lumen_m3_openapi.yaml 2.0.0-m3 with explicit operationIds; NestJS and Flutter codegen track the file.

**Consequences:** Positive: traceable WI-013–WI-026 scope. Negative: larger swagger surface to maintain.

### ADR-004: Stock and reservations at variant granularity
**Context:** Lighting SKUs vary by finish and wattage.

**Decision:** Unchanged — reservations on checkout, release on payment failure/expiry.

**Consequences:** Positive: prevents overselling. Negative: cart lines always reference variantId.

### ADR-005: Guest cart header plus merge on login
**Context:** US-005 and guest checkout require anonymous carts without forcing registration first.

**Decision:** Issue GuestCart UUID returned to client; client sends X-Guest-Cart-Id on cart/checkout routes; mergeGuestCart combines into signed-in Cart after login.

**Consequences:** Positive: seamless guest-to-customer upgrade. Negative: clients must persist guest cart id securely.

### ADR-006: Mock payment instead of Stripe for Release 2
**Context:** Stakeholder demo needs full checkout without PCI scope or Stripe test keys in M3.

**Decision:** confirmMockPayment and MockPaymentSession gate paid transition; Stripe columns nullable for a later milestone.

**Consequences:** Positive: faster M3 delivery and simpler mobile UX. Negative: production launch requires payment provider swap and webhook work.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.