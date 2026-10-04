# Architecture

beauty-mvp release 1 is a Flutter demo app for iOS and Android with three functional screens: Browse (with category filter), Product Detail and Cart. It runs fully offline. There is no live backend in this release. The catalog is a bundled, versioned JSON asset of 20-30 products, and all product images are bundled too. The cart is an in-memory Riverpod Notifier that is lost when the app process ends.

The design keeps a seam for the future. Presentation and state code depend only on a CatalogRepository interface in the domain layer. Release 1 binds that interface to LocalCatalogRepository, which reads the JSON asset. A later phase can bind it to ApiCatalogRepository, backed by the dart-dio client generated from the OpenAPI document, without touching screens or state.

The OpenAPI 3.1 document remains the contract. It contains one operation, the infrastructure health check GET /api/v1/health, because the PRD states there are no API operations in this release. It also defines the shared schemas that the bundled catalog JSON must conform to: Error, Money, Category, Product, ProductImage, Catalog and the ProductPage pagination envelope. The bundled file is therefore the same shape a future GET /products endpoint will return, and CI validates the asset against these schemas.

An optional NestJS stub service exposes only the health check and holds a minimal Prisma schema (Category, Product) that mirrors the catalog shape. It is not required for the demo and is not called by the app.

The following project conventions are deferred, as the PRD's Assumptions section records:
- Accounts, JWT, signed-in carts, stock per variant, orders and Stripe. They will be applied when checkout, accounts or backend phases are approved.
- Money is held as integer minor units (cents) plus the ISO 4217 code USD everywhere. Formatting uses integer arithmetic only.

## Components
- **Mobile app (beauty_mvp)** (Flutter 3.x (Dart 3), flutter_riverpod (Notifier/AsyncNotifier), go_router, freezed + json_serializable, intl (en_US), flutter_test, integration_test): Single Flutter codebase for iOS 14+ and Android 8 (API 26)+, phones in portrait only. Renders Browse, Product Detail and Cart, plus an optional native splash. Holds all business logic for this release: catalog loading and validation, category filtering, quantity rules (1-10 per line, merge on add, cap at 10) and integer-cent totals. Feature-first structure: lib/features/catalog and lib/features/cart, each with data, domain and presentation folders. Shared code (theme tokens, router, widgets, money formatting) lives in lib/core.
- **Bundled catalog asset** (JSON asset declared in pubspec.yaml; JSON Schema validation in CI using the components from openapi.yaml): assets/catalog/catalog.json holds the object {schemaVersion, currency, categories[], products[]}, conforming to the OpenAPI Catalog schema. Each product has id, name, brand, categoryId, price {amountMinor, currency}, shortDescription, keyIngredients and/or usageNotes, and image {src, alt}. It is supplied by the business using a team template (spreadsheet converted to JSON). Validated in CI against the OpenAPI schemas.
- **Bundled product images** (Flutter asset bundle, Image.asset with errorBuilder/frameBuilder, precacheImage): assets/images/products/<productId>.webp (or .jpg). Images are pre-resized to at most 1080 px on the long edge and at most 200 KB each. Display is decoded at tile size using cacheWidth/ResizeImage, and the first screen of tiles is precached so the grid scrolls at 60 fps. A tokenized placeholder is shown on error or while decoding.
- **Design system (lib/core/theme)** (Flutter ThemeData + ThemeExtension (AppTokens), bundled font files (no runtime font download)): Design tokens from the approved style proposal (WI-001): color palette, typography scale (body at least 14 sp), spacing, radii, elevation and the logo asset. Builds ThemeData for both platforms. Widgets never hard-code colors or sizes. The token set is checked for 4.5:1 text contrast.
- **Router (lib/core/router)** (go_router): Defines one route per screen.
- '/' is Browse.
- '/products/:productId' is Product Detail, a child route of '/'. It is pushed on top of Browse, so Browse keeps its scroll position and filter.
- '/cart' is Cart.
Unknown product ids redirect to a not-found state with a back-to-Browse action.
- **API contract (openapi.yaml)** (OpenAPI 3.1 YAML, openapi-generator (dart-dio), Spectral lint in CI): Single source of truth for HTTP contracts and shared data shapes. Release 1 contains only GET /api/v1/health, plus the reusable schemas that the catalog JSON follows. packages/api_client is generated from it (dart-dio) and kept in the repo, but the app does not call it in release 1.
- **Stub API service (optional, not used by the demo)** (NestJS (TypeScript), @nestjs/config, @nestjs/terminus, @nestjs/swagger, Prisma ORM, PostgreSQL 16, Jest + Supertest, Docker): Keeps the backend skeleton ready for later phases. Exposes only GET /api/v1/health, which returns 200 when PostgreSQL is reachable and 503 otherwise. Runs in docker-compose for staging. No product, cart, order, auth or payment endpoints in this release.
- **CI/CD** (GitHub Actions, Docker, docker-compose (staging)): Runs on every pull request:
- flutter analyze, unit, widget and integration tests
- catalog.json schema validation and an image-exists check for every product
- OpenAPI lint
- stub service lint, test and Docker build
Produces debug and release demo builds: Android APK/AAB and an iOS build for TestFlight or ad-hoc install.

## Backend modules
### health
Liveness/readiness check for the optional stub service. Performs SELECT 1 through PrismaService. Returns 200 {status:'ok', database:'up'} when reachable and 503 with the shared Error schema otherwise. Unauthenticated.
Entities: 

- `GET /api/v1/health`

### prisma (infrastructure, shared)
PrismaService wrapper (connect on module init, graceful shutdown). Owns the minimal Category/Product schema that mirrors the bundled catalog, so a later catalog module can serve GET /api/v1/products without a data-model rewrite. No controllers in this release.
Entities: Category, Product


## Mobile app features
- catalog (Browse + Product Detail): screens BrowseScreen (route '/'): logo app bar with a cart icon and a badge showing total units. The cart icon is a 48dp target, labelled 'Cart, N items'. Below it sits a horizontally scrollable category ChoiceChip row: All, Skincare, Makeup, Haircare, Fragrance, with All selected by default and the selected chip highlighted. Then a 2-column SliverGrid of ProductTiles showing image with placeholder, name, brand and USD price.
- Loading: skeleton tiles.
- Empty: 'No products in this category' with a Show all action.
- Error: friendly message with a Retry button that invalidates catalogProvider.
- No search or sort controls., ProductDetailScreen (route '/products/:productId'): large image with a semantic label from image.alt, name, brand, price, short description, and 'Key ingredients' and/or 'How to use' sections.
- QuantitySelector: 1-10. The decrease control is disabled at 1 and the increase control is disabled at 10. Buttons are 48dp and labelled.
- Full-width Add to Cart button. Adding shows a SnackBar confirmation, or a 'Maximum 10 per item' message when the merge was capped.
- The app bar cart badge updates on add.
- No stock, variants, reviews or wishlist.
- Loading, error and not-found states (unknown id) each offer a back to Browse action. (state: Providers:
- catalogRepositoryProvider: Provider<CatalogRepository>, bound to LocalCatalogRepository(rootBundle).
- catalogProvider: AsyncNotifier<Catalog>. Loads and validates catalog.json once and keeps it cached for the session. Retry calls ref.invalidate(catalogProvider).
- selectedCategoryProvider: Notifier<CategoryFilter>. Values are all or categoryId; defaults to all. It lives above the router, so it survives navigating to Detail and back.
- filteredProductsProvider: Provider<AsyncValue<List<Product>>>. Derived from catalogProvider and selectedCategoryProvider, preserving catalog order.
- productByIdProvider: Provider.family<AsyncValue<Product?>, String>.
- productQuantityProvider: AutoDispose Notifier.family<int, String>. Local selector state (1-10) per Detail screen instance. It resets to 1 on each open.

Browse scroll position is preserved because Detail is pushed on top of Browse (Browse stays mounted), with a PageStorageKey on the grid.

Domain models are freezed with json_serializable: Catalog, Category, Product, ProductImage and Money. Their JSON shape matches the OpenAPI Catalog, Category, Product, ProductImage and Money schemas.)
- cart: screens CartScreen (route '/cart'): list of CartLineTiles. Each shows image, name, brand, unit price, a QuantitySelector (1-10), the line subtotal and a Remove button (48dp, labelled 'Remove <name>'). An overall Total row in USD is the last element. There is no checkout, payment, promo, shipping or tax element below it.
- Empty state: 'Your cart is empty' with a Browse products action that navigates to '/'. No total is shown when empty.
- Loading and error states apply while the catalog is resolving, because lines look up product data from the catalog. (state: cartProvider: Notifier<Cart> (not autoDispose, in memory only, never persisted).

Cart is an immutable freezed value. It holds an ordered list of CartLine {productId, quantity}, keyed by productId. Operations:
- add(productId, qty) returns AddResult {added, capped}. If a line exists, it merges: newQty = min(existing + qty, 10) and capped = existing + qty > 10. Otherwise it inserts min(qty, 10).
- setQuantity(productId, qty): clamps to 1..10.
- remove(productId).
- clear(): used by tests.

CartLine stores only productId and quantity. Display data (name, brand, image, unit price) is resolved from the catalog through cartViewProvider.

Derived providers:
- cartViewProvider: Provider<AsyncValue<List<CartLineView>>>. Joins cart lines with the catalog and computes lineSubtotalMinor = unitPrice.amountMinor * quantity as an int.
- cartItemCountProvider: Provider<int>. Sum of quantities, drives the badge.
- cartTotalProvider: Provider<Money>. Integer sum of line subtotals in USD.

All updates are synchronous, well under the 100 ms target.)

## Data model
1. Money
Prices are Money {amountMinor: int (cents, >= 0), currency: ISO 4217 string, 'USD' only in release 1}. Line subtotal = amountMinor * quantity. Total = sum of line subtotals. All arithmetic uses Dart int, so there is no rounding.
MoneyFormatter.format(Money) uses integer arithmetic only:
- dollars = amountMinor ~/ 100, grouped with en_US separators via intl NumberFormat.decimalPattern on the integer
- cents = (amountMinor % 100) padded to 2 digits
- output is '$' + dollars + '.' + cents, for example 2450 -> $24.50 and 123456 -> $1,234.56
Floats are never used for storage or computation.

2. Catalog JSON (assets/catalog/catalog.json)
The file is {schemaVersion: 1, currency: 'USD', categories: Category[], products: Product[]}.
- Category is {id, name, sortOrder}. The ids are the fixed set skincare, makeup, haircare, fragrance, displayed as Skincare, Makeup, Haircare, Fragrance. 'All' is a UI filter value, not a category.
- Product is {id (stable slug, e.g. 'hydra-glow-serum'), name, brand, categoryId (exactly one, must reference a category), price: Money, shortDescription, keyIngredients: string|null, usageNotes: string|null, image: {src: asset path relative to assets/images/products/, alt: screen-reader text}}.
- At least one of keyIngredients or usageNotes is required.

3. Validation on load (LocalCatalogRepository)
- Missing file or unparseable JSON, a wrong schemaVersion, or zero valid products each throw CatalogLoadException. The UI then shows the error state with Retry.
- A single product failing validation is skipped and logged in debug builds only, so one bad record cannot blank the demo. Failure causes are a duplicate id, an unknown categoryId, a non-integer or negative amountMinor, a currency other than USD, or a missing required field.
- CI validates the asset strictly (schema plus every image file exists), so skipped products should never ship.

4. Extensibility
- New optional fields can be added without breaking older parsing. json_serializable is configured to ignore unknown keys.
- Variants: a future variants[] array of {id, sku, name, price, stock} can be added to Product. CartLine gains an optional variantId, and the merge key becomes (productId, variantId). Product-level price becomes the 'from' price.
- Signed-in carts, orders with copied name and unit price, stock reservation and Stripe follow the project conventions when those phases start.

5. Server-side mirror
The Prisma schema (optional stub) mirrors the same shape: products.price_minor INT plus currency CHAR(3), and categories with a FK from products. Seeding from catalog.json is therefore a straight mapping.

6. Pagination
The ProductPage schema {items, total, page, pageSize} is defined in the contract for the future GET /products endpoint. It is not used in release 1, because the full 20-30 product catalog is loaded at once.

## Security
- No personal data: the app has no accounts, sign-in, forms or free-text inputs, and collects, stores and transmits no personal data. Account deletion and password hashing conventions are not applicable in release 1.
- No persistent storage: the cart is in memory only. Nothing is written to SharedPreferences, files, databases or flutter_secure_storage in release 1. flutter_secure_storage is reserved for tokens in the accounts phase.
- No network use by the app: catalog and images are bundled assets, and the app makes no HTTP calls. The release Android manifest does not declare the INTERNET permission (Flutter only adds it to the debug and profile manifests). iOS has no ATS exceptions in release.
- Transport rules for later phases are set up now:
- android/app/src/debug/res/xml/network_security_config.xml allows cleartext only for 10.0.2.2, so debug builds can reach the local staging stub at http://10.0.2.2:3000.
- The main/release config is https-only, with cleartextTrafficPermitted=false.
- No analytics, crash-reporting, advertising or tracking SDKs. Dependencies are limited to the approved list and checked in CI (flutter pub outdated, and dependabot for pub and npm). No consent flow is needed.
- No payment or card data is handled; there is no Stripe SDK in release 1.
- Supply chain and integrity:
- catalog.json and images come from the business and are validated in CI: schema, image existence and size limits.
- Text is rendered as plain Text widgets (no HTML/markdown rendering), so no injection surface exists.
- Release builds use code obfuscation (--obfuscate --split-debug-info), with symbols kept privately in CI artifacts. Signing keys and keystore passwords live only in GitHub Actions secrets, never in the repo.
- Optional stub service: config comes from environment variables validated at startup with @nestjs/config and Joi (DATABASE_URL, PORT, NODE_ENV). It uses helmet and a restrictive CORS policy (none needed for mobile). GET /health exposes no version, stack traces or connection details, and errors use the shared {statusCode, error, message} shape. The Docker image runs as a non-root user. No secrets are in code or images.
- Forward-looking: the OpenAPI document already declares the bearerAuth (JWT) security scheme as the global default, so every future endpoint is authenticated unless it explicitly opts out, as /health does with security: [].

## Architecture decisions
### ADR-001: No live backend in release 1; local catalog behind a repository interface
**Context:** The PRD scopes release 1 to an offline stakeholder demo, with explicit statements:
- No backend, no server-side APIs, no Stripe.
- The catalog is a bundled JSON file plus images.
- The codebase must later swap in a backend without a rewrite.
The target stack and conventions assume NestJS/Prisma/PostgreSQL and a generated dart-dio client.

**Decision:** The app ships with LocalCatalogRepository, which implements a domain-level CatalogRepository interface (Future<Catalog> loadCatalog()). It reads assets/catalog/catalog.json. Screens and Riverpod providers depend only on the interface via catalogRepositoryProvider.

The NestJS service is kept as an optional stub with only GET /api/v1/health. The app never calls it in release 1.

When a backend phase starts, add ApiCatalogRepository using packages/api_client and override the provider binding.

**Consequences:** Positive:
- Zero runtime dependency on servers or networks during the demo.
- Fast cold start.
- No hosting cost.
- Deterministic tests.

Negative:
- Catalog changes need a new app build.
- The generated API client is unused for now.
- The mobile convention 'HTTP only through the generated client' is satisfied trivially, because there is no HTTP.

The backend skeleton, CI and docker-compose exist, so the next phase starts from a working baseline.

### ADR-002: OpenAPI stays the contract: health-only operations plus shared schemas that the bundled catalog must match
**Context:** Contract-first design is a project rule. The PRD has no API operations, but the data model must be easy to move behind an API later. Without a shared definition, the local JSON shape and a future API response would drift.

**Decision:** openapi.yaml (OpenAPI 3.1) contains one operation, getHealth (GET /api/v1/health), which is unauthenticated. It also defines the reusable component schemas Error, HealthStatus, Money, Category, ProductImage, Product, Catalog and ProductPage, plus the page and pageSize parameters and the bearerAuth scheme as the global default.

The bundled catalog.json must validate against the Catalog schema, which CI enforces. The Flutter freezed models use the same field names.

Future endpoints such as GET /products (returning ProductPage) and GET /products/{productId} (returning Product) will reuse these schemas unchanged.

**Consequences:** Positive:
- One definition of product data for the app, the future API and the Prisma seed.
- Moving to a backend changes the data source, not the model.

Negative:
- A few schemas are unused by operations in release 1.
- Spectral must be configured not to fail on unused components.

Keeping only the health check respects the scope limit and the PRD's explicit 'no API operations' assumption.

### ADR-003: Money as integer minor units with integer-only formatting
**Context:** Project conventions and the PRD require prices in integer cents with an ISO 4217 code, never floats. Totals must be exact. Common helpers such as NumberFormat.currency.format(double) require converting to double.

**Decision:** Money is a freezed value {int amountMinor, String currency}. Rules:
- Line subtotal = amountMinor * quantity, and total = the sum, both in int.
- Currency mixing throws, which is only relevant in future phases.
- MoneyFormatter renders strings with integer division and modulo (dollars = amountMinor ~/ 100, cents = amountMinor % 100 padded to two digits). Thousands grouping is applied to the integer dollars.
- The formatter is unit tested, for example 0 -> $0.00, 5 -> $0.05, 2450 -> $24.50 and 123456 -> $1,234.56.

The Prisma schema mirrors this with price_minor INT and currency CHAR(3).

**Consequences:** Positive:
- No floating-point rounding anywhere.
- The same representation works in JSON, Dart, TypeScript and PostgreSQL.
- Ready for Stripe, which uses minor units.

Negative:
- The formatter is custom, but it is tiny and covered by tests.
- A multi-currency phase will need per-currency minor-unit exponents, for example JPY = 0. That is out of scope now.

### ADR-004: In-memory cart as a Riverpod Notifier keyed by productId, storing only ids and quantities
**Context:** The cart must survive navigation but not app restarts. It has no accounts, persistence or stock. It needs a merge-on-add rule capped at 10 units, quantity limits of 1-10, a unit-count badge and updates within 100 ms. Later phases will add server-side signed-in carts and variants.

**Decision:** cartProvider is a non-autoDispose Notifier<Cart> scoped to the root ProviderScope. Cart is an ordered list of CartLine {productId, quantity}; its operations add, setQuantity and remove enforce clamping to 1..10. The add merge returns AddResult.capped so the UI can show a 'maximum 10 per item' message.

Product display data and price are joined from the catalog at render time (cartViewProvider). Price is not copied into the line, because release 1 has no orders and a static catalog.

Nothing is persisted.

**Consequences:** Positive:
- Simple, synchronous, easily unit-tested business rules.
- Restarting the app empties the cart, as required.

Negative:
- Lines referencing a product missing from the catalog are dropped from the view. This cannot happen in practice, because the catalog is static per build.

Future phases:
- Replace the notifier's backing with a CartRepository (local now, API later).
- Add variantId to CartLine.
- Copy name and unit price into order lines at checkout, per project conventions.

### ADR-005: Bundled, pre-sized images with decode-size limits and placeholders
**Context:** The NFRs require a 3-second cold start, 60 fps grid scrolling, placeholders while loading and no crashes on image failure. Images are supplied by the business at arbitrary sizes, and demo devices include a mid-range Android phone.

**Decision:** Image handling:
- A CI or script step resizes supplied images to at most 1080 px on the long edge in WebP or JPEG, targeting 200 KB or less each, and fails the build if a referenced file is missing.
- Tiles use Image.asset with cacheWidth computed from tile width times devicePixelRatio. They use frameBuilder for a fade-in over a token-colored placeholder, and errorBuilder for a branded placeholder icon with a semantic label. Name, brand and price stay visible either way.
- Visible first-row images are precached after the catalog loads.
- There is no network image library in release 1. cached_network_image is the planned drop-in when images move to a CDN.

**Consequences:** Positive:
- Predictable memory use and smooth scrolling.
- No network dependency.

Negative:
- App size grows by roughly 30 x 200 KB, about 6 MB, which is acceptable for a demo.

The image.src field is an asset path now and becomes a URL later, handled by ApiCatalogRepository.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.