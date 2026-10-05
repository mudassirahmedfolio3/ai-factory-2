# Architecture

ShopEase M1 is a speed demo: a single Flutter app for Android that runs on an emulator with no backend, network, login or secrets. It reads a bundled local mock catalog (assets/mock/catalog.json, 12-20 products with size/color variants, per-variant integer-cent USD prices and per-variant stock). It has exactly 3 screens: Product List (initial route '/'), Product Detail ('/products/:productId') and an optional in-memory Cart ('/cart').

The app is built feature-first: lib/features/catalog and lib/features/cart, each with data/domain/presentation. Shared code lives in lib/core: theme tokens, go_router config, l10n (a single English (US) ARB string source), money formatting and shared widgets. State uses Riverpod Notifier/AsyncNotifier.

The catalog is accessed only through a CatalogRepository interface. In M1 the only implementation is MockCatalogRepository, which parses the bundled JSON. That JSON has exactly the same shape as the ProductSummary/ProductDetail schemas in the OpenAPI contract. In a later milestone an ApiCatalogRepository backed by the generated packages/api_client (dart-dio) replaces it with no change to domain or presentation code.

The OpenAPI 3.1 contract is intentionally minimal:
- GET /api/v1/health (infrastructure, not counted toward the operation limit).
- Two optional, read-only catalog operations (listProducts, getProduct) that define the future server shape.

The NestJS backend and PostgreSQL are NOT built or required in M1. Only the contract and a catalog-only Prisma schema are defined, so the next milestone can start without guessing.

Auth, users, cart persistence, orders and Stripe payments are deferred to later milestones. They will follow the project conventions:
- JWT 15-minute access tokens plus refresh tokens.
- Order status flow pending_payment -> paid -> fulfilled -> delivered, plus cancelled and refunded.
- Stripe PaymentIntents confirmed by webhook.
- Order lines snapshot name and unit price.

## Components
- **ShopEase Flutter app (Android)** (Flutter 3.x (Dart), Riverpod (Notifier/AsyncNotifier), go_router, freezed/json_serializable, intl, flutter_localizations (gen-l10n)): The only runtime component in M1. Renders Product List, Product Detail and Cart screens from the bundled mock catalog. Formats money from integer minor units plus the ISO 4217 code. Holds the cart in memory. Must cold-start to the first rendered list in under 3 seconds with no network.
- **Bundled mock catalog** (JSON asset loaded via rootBundle; WebP images, each under 50 KB): Static JSON asset (assets/mock/catalog.json) with 12-20 products, each with size/color variants, per-variant priceMinor/currency (USD) and stockQuantity. It includes at least one product with every variant out of stock and at least one variant out of stock on an otherwise available product. Its shape equals the OpenAPI ProductDetail schema. Product images are small bundled WebP assets under assets/images/products/ or a generated placeholder when imageUrl is null.
- **lib/core (shared app foundation)** (Flutter/Dart, intl, go_router, Riverpod): Provides:
- Design tokens and ThemeData (colors, typography, spacing, radii, min touch target 48dp) chosen by the agent and meeting WCAG AA contrast.
- go_router configuration with one route per screen.
- The single English (US) string source (lib/l10n/app_en.arb).
- MoneyFormatter, built on intl NumberFormat.simpleCurrency(name: currency) over integer minor units using the currency's decimal digits and no floating-point arithmetic on amounts.
- Shared widgets: ProductImage, PriceText, StockBadge, and the LoadingView/EmptyView/ErrorView state widgets.
- The network folder, reserved for the generated client wiring in later milestones.
- **packages/api_client (generated)** (openapi-generator dart-dio): Dart client generated from openapi.yaml. Committed to the repo so the contract is exercised by codegen in CI, but not wired into the app in M1 (the app makes no HTTP calls). It becomes the only HTTP path when ApiCatalogRepository is introduced.
- **ShopEase API (deferred; optional health only)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, Prisma ORM, Jest + Supertest): Future NestJS REST API with global prefix /api/v1. In M1 nothing is required. If a backend skeleton is started, it exposes only GET /api/v1/health (200 when the DB is reachable). Catalog read endpoints follow the contract in the next milestone.
- **PostgreSQL (deferred)** (PostgreSQL 16 via docker-compose (staging)): Future system of record for catalog (products, variants, per-variant stock), and later users, carts, orders and payments. Not used in M1.
- **CI pipeline** (GitHub Actions): Runs on every push/PR:
- flutter pub get
- flutter gen-l10n
- dart run build_runner build
- flutter analyze (zero errors)
- flutter test (price formatting, catalog loading, cart subtotal and screen widget tests)
- flutter build apk --debug

It also validates openapi.yaml with a linter (Redocly/Spectral).

## Backend modules
### health
Infrastructure liveness and readiness. Returns 200 with status ok when a trivial 'SELECT 1' via PrismaService succeeds, and 503 with the shared error body otherwise. Unauthenticated; exposes no version, hostnames or stack details. Optional in M1; the app does not depend on it.
Entities: 

- `GET /api/v1/health`

### catalog
Read-only public catalog (contract defined now, implemented in the next milestone; not built in M1). Lists active products with pagination (page, pageSize; returns items and total) and returns product detail with variants, per-variant price (integer minor units + ISO 4217 currency) and per-variant stock. The controller stays thin; CatalogService maps Prisma rows to the ProductSummary/ProductDetail DTOs exactly as in OpenAPI. It computes priceFrom as the minimum active-variant price and inStock as any active variant with stockQuantity > 0.
Entities: Product, ProductVariant

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`

## Mobile app features
- catalog (browse and product detail): screens ProductListScreen - route '/' (initial route): scrollable ListView.builder of product cards (image or placeholder with semantic label, name, 'from' price formatted from integer cents via currency code, out-of-stock badge when no variant has stock). App bar has a cart icon with an item-count badge (48dp, semantic label). Handles loading, empty ('No products available') and error (retry) states. Scroll position is preserved via a PageStorageKey plus pushing the detail route on top of the list, so the list stays mounted., ProductDetailScreen - route '/products/:productId': image, name, description, price of the selected variant (or priceFrom before a selection), size and color choice chips (48dp targets, selected state highlighted and announced via Semantics(selected: true)), and the selected variant's in-stock/out-of-stock status. 'Add to cart' is disabled until an in-stock variant is selected and stays disabled for out-of-stock variants. Handles loading, not-found/error and 'no variants' states. System back and the app bar back button pop to the list. (state: All providers are Riverpod.
- catalogRepositoryProvider (Provider<CatalogRepository>) returns MockCatalogRepository in M1. It loads and parses assets/mock/catalog.json once on a background isolate via compute() and caches it in memory.
- productListProvider is an AsyncNotifier<List<ProductSummary>> built from the repository.
- productDetailProvider is an AsyncNotifierProvider.family<ProductDetail, String> keyed by productId.
- variantSelectionProvider is a NotifierProvider.family<VariantSelection, String> keyed by productId. It holds the selected size and color and exposes the resolved ProductVariant? (a variant matching both the size and the color). It is autoDispose so selection resets when leaving the screen.
- Domain models (ProductSummary, ProductDetail, ProductVariant, Money) are freezed/json_serializable classes whose JSON matches the OpenAPI schemas.)
- cart (in-memory, optional): screens CartScreen - route '/cart': one line per variant showing product name, variant label (size / color), unit price, quantity stepper (48dp +/- buttons with semantic labels) and line total, plus a subtotal. All arithmetic is integer cents and display uses MoneyFormatter with USD. Removing a line or reducing quantity to 0 removes it; an empty cart shows an empty-state message with a 'Browse products' action. There are no checkout or payment actions. (state: cartProvider is a Riverpod Notifier<CartState>, kept alive for the process lifetime and never persisted, so the cart is lost when the app process closes.
- CartState holds an immutable list of CartLine records: variantId, productId, productName, variantLabel, unitPrice (Money snapshot copied at add time, order-line style), and quantity (int >= 1).
- Methods: add(ProductDetail, ProductVariant) increments quantity if the variantId already exists, otherwise appends; setQuantity(variantId, qty) removes the line when qty <= 0; remove(variantId). Quantity is capped at the variant's stockQuantity as known at add time.
- Derived providers: cartItemCountProvider (sum of quantities, drives the app bar badge) and cartSubtotalProvider (Money; sum of unitPrice.amountMinor * quantity as int). All lines must share one currency; the Notifier asserts this.)

## Data model
Money: every price is an integer amount in minor units (cents) plus an ISO 4217 currency code, as Money { amountMinor: int, currency: 'USD' } in the API and app, and price_minor INTEGER plus currency CHAR(3) in PostgreSQL. No double or float is ever used for money. Display uses intl NumberFormat.simpleCurrency(name: currency) with decimalDigits from the currency. The major-unit value for display is produced by NumberFormat on amountMinor / 10^digits only at the formatting boundary inside MoneyFormatter, which is unit-tested (1999 USD -> '$19.99', 0 -> '$0.00', 100000 -> '$1,000.00'). Symbols are never hard-coded.

Stock: tracked per ProductVariant (stockQuantity >= 0). A product is out of stock when no active variant has stockQuantity > 0. Stock reservation at checkout (reserve on checkout, release on failed or expired payment) is deferred and will add a reservation mechanism on ProductVariant in a later milestone.

Variants:
- Each variant has an optional size and an optional color. Products may use one or both dimensions.
- (productId, size, color) is unique. Postgres treats NULLs as distinct, so the service layer also validates uniqueness for single-dimension products; alternatively a NULLS NOT DISTINCT unique index can be added via raw SQL migration.
- The price lives on the variant; the product exposes a derived priceFrom (minimum variant price).

Mock catalog: assets/mock/catalog.json is { "items": ProductDetail[] }, using the exact OpenAPI field names and fixed UUIDs, so the future API swap is a repository change only. imageUrl may be a bundled asset path (assets/images/products/*.webp) or null. The ProductImage widget renders Image.asset for 'assets/' paths, Image.network for http(s) URLs (later milestones) and a token-styled placeholder for null. imageAlt is always present for semantic labels.

Cart lines: copy productName, variantLabel and unitPrice at the time of adding (order-line snapshot semantics), so they would not change if the catalog changed.

Deferred entities, not in this schema by scope rule and to be added in later milestones: User, Address, Category, Cart, CartItem, Order, OrderItem (with name and unit price snapshots), Payment (Stripe PaymentIntent id and status). OrderStatus will be an enum: pending_payment, paid, fulfilled, delivered, cancelled, refunded.

DB-level CHECK constraints (price_minor >= 0, stock_quantity >= 0, currency ~ '^[A-Z]{3}$') are added in the initial SQL migration, because Prisma schema cannot express them.

## Security
- M1 collects no personal data: no accounts, authentication, payment data, analytics, crash reporting with PII or tracking SDKs. Nothing is stored on device except in-memory cart state that dies with the process.
- M1 makes no network calls. The app's data path uses only bundled assets. The release AndroidManifest does not need to declare INTERNET for M1; if it is added for future readiness, the release network-security config remains HTTPS-only (cleartextTrafficPermitted=false).
- Debug-only emulator access follows project convention. android/app/src/debug/res/xml/network_security_config.xml permits cleartext only for the domain 10.0.2.2 and is referenced only from the debug manifest overlay. Release builds use the default HTTPS-only policy.
- No secrets are committed. M1 requires none. Future configuration (API base URL, Stripe publishable key) is injected via --dart-define per flavor on the app side and environment variables validated at startup with @nestjs/config on the backend. .env files are git-ignored.
- Dependencies are pinned via pubspec.lock (committed). CI runs flutter analyze with zero errors, and Dependabot/renovate is enabled for pub and GitHub Actions.
- Public, unauthenticated API surface is limited to read-only catalog and health. The health endpoint returns no version, host, stack traces or DB details. All errors use the shared { statusCode, error, message } body without internal details.
- A bearerAuth (JWT) security scheme is declared in the contract for future milestones (15-minute access tokens and refresh tokens; access token stored with flutter_secure_storage). No M1 operation requires it, which is stated explicitly with security: [].
- Future backend hardening baseline:
- Helmet.
- Strict CORS allow-list.
- Global ValidationPipe with whitelist and forbidNonWhitelisted.
- Rate limiting via @nestjs/throttler on public endpoints.
- pageSize capped at 100.
- productId validated as UUID (400 on malformed input).
- Parameterized queries via Prisma only.
- Future payments: Stripe PaymentIntents in test mode. The server creates the intent, the app confirms it with the Stripe SDK, and a signature-verified webhook marks the order paid. Card data never touches our servers. Future personal data: minimal fields, passwords hashed with argon2id, and account deletion supported.
- Accessibility and safety of UI: all interactive elements have semantic labels and 48dp targets. No user-generated content is rendered in M1.

## Architecture decisions
### ADR-001: M1 reads a bundled local mock catalog behind a repository interface
**Context:** The PRD requires the app to run on an Android emulator immediately, offline, with no backend, network, login or secrets, and to show the product list in under 3 seconds. Building the NestJS/PostgreSQL catalog now would slow delivery and add setup for the demo reviewer. Later milestones must switch to the real API without rewriting screens.

**Decision:** Ship assets/mock/catalog.json inside the app and load it through a CatalogRepository interface (MockCatalogRepository in M1). The JSON uses exactly the OpenAPI ProductDetail schema (same field names, Money objects, UUIDs), and parsing reuses the same freezed/json_serializable domain models. The parse runs once via compute() and is cached in memory.

**Consequences:** Positive:
- Zero-setup demo with deterministic data.
- Fast cold start.
- Screen and widget tests use the same repository and can override it with a fake via ProviderScope overrides.

Negative:
- Stock and prices are static.
- Catalog changes require an app rebuild.
- The generated api_client is not exercised at runtime in M1.

The next milestone adds ApiCatalogRepository using packages/api_client and swaps the provider, with no presentation changes.

### ADR-002: Money as integer minor units with ISO 4217 currency; formatting derived from the currency code
**Context:** Project rules forbid floating-point money and hard-coded currency symbols; prices must be stored as cents with a currency code. The demo must display 1999 cents as $19.99 and compute cart subtotals exactly.

**Decision:** Represent money everywhere as Money { amountMinor: int, currency: String }:
- API: integer, int32.
- Database: INTEGER price_minor plus CHAR(3) currency.
- App: freezed class.

All arithmetic (line totals, subtotal) is integer multiplication and addition on amountMinor. Display goes only through lib/core MoneyFormatter, which uses intl NumberFormat.simpleCurrency(name: currency) with the currency's decimal digits and the device locale defaulting to en_US. It is covered by unit tests.

**Consequences:** Positive:
- Exact totals.
- Multi-currency readiness without code changes to widgets.
- No symbols in string resources.

Negative:
- Every price field is an object rather than a number, which is slightly more verbose.
- Mixed-currency carts are not supported (asserted in the cart Notifier), which is acceptable because M1 is USD only.
- INTEGER caps a single price at about $21M, which is ample for retail.

### ADR-003: In-memory cart as a Riverpod Notifier with order-line snapshots
**Context:** US-003 (could) needs add-to-cart, quantity changes, removal and subtotal with no sign-in, payment or persistence. Project rules say carts belong to signed-in users and that order lines copy name and unit price. Cart persistence is out of scope for M1.

**Decision:** Implement cartProvider as a keep-alive Notifier<CartState> holding CartLine snapshots: productName, variantLabel and the unitPrice Money are copied at add time, keyed by variantId. Derived providers expose item count and subtotal. There is no persistence and no checkout actions.

**Consequences:** Positive:
- Tiny, fully unit-testable logic (subtotal test required by the PRD).
- The snapshot shape maps directly onto future CartItem/OrderItem entities.

Negative:
- The cart is lost on process death, which is explicitly expected.
- There is no server-side stock validation; quantity is capped only by mock stockQuantity.

When auth arrives, the cart moves server-side (Cart/CartItem per user) and the Notifier becomes an AsyncNotifier over the API.

### ADR-004: Minimal contract-first OpenAPI 3.1 with health plus two read-only catalog operations
**Context:** Scope limits allow at most 4 API operations, plus the health check, and no backend work in M1 if it slows delivery. The team designs contract-first and generates the Dart client from OpenAPI. The mock catalog should not drift from the future server shape.

**Decision:** Publish openapi.yaml with:
- GET /api/v1/health (getHealth).
- GET /api/v1/products (listProducts, page/pageSize pagination returning items and total).
- GET /api/v1/products/{productId} (getProduct).

The contract also includes the shared Error schema { statusCode, error, message }, a declared bearerAuth scheme unused by these public operations, and Money/ProductSummary/ProductDetail/ProductVariant schemas. The mock JSON conforms to ProductDetail. CI lints the spec and regenerates packages/api_client.

**Consequences:** Positive:
- The next milestone implements the catalog module against a frozen contract.
- The mock data is validated against the same schema.
- The client generates cleanly (no oneOf in the used schemas).

Negative:
- Two operations are specified before they are implemented. This is acceptable because they are read-only and low risk.

Auth, cart, orders and payments endpoints are added in later contract versions.

### ADR-005: go_router with push navigation to preserve list scroll position; one route per screen
**Context:** US-002 requires returning from detail to the list at the same scroll position via app back or system back. Conventions require go_router with one route per screen spec, and at most 3 screens.

**Decision:** Define three GoRoutes in lib/core/router:
- '/' ProductListScreen.
- '/products/:productId' ProductDetailScreen.
- '/cart' CartScreen.

The list opens detail and cart with context.push, so the list route stays mounted beneath them. The list also uses a PageStorageKey on its ListView.builder as a safety net. The detail screen reads the productId path parameter and loads via productDetailProvider.

**Consequences:** Positive:
- Correct back-stack behaviour with Android system back.
- Deep-linkable detail routes.
- Scroll position preserved without extra state.

Negative:
- The list stays in memory while detail is open, which is negligible for 12-20 products.

Integration tests verify list -> detail -> back preserves the scroll offset.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.