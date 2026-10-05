# Architecture

Speed Demo MVP (M1) for the lighting e-commerce app. It is a single Flutter 3.x app for Android first, and the same codebase can later target iOS. The app runs fully offline from a bundled mock catalog. M1 has no backend dependency, no auth, no payments, no checkout and no personal data. There are three screens: Product List (/products), Product Detail (/products/:productId) and an optional in-memory Cart (/cart).

The architecture is built so the mock catalog can be swapped for the real API later without touching presentation code:
(1) Widgets depend only on Riverpod providers.
(2) Providers depend only on an abstract CatalogRepository with a paginated fetchProducts(page, pageSize) returning {items, total, page, pageSize} and a getProduct(productId).
(3) M1 binds CatalogRepository to MockCatalogRepository. It loads assets/mock_catalog.json once through rootBundle and serves pages from memory.
(4) A later release binds CatalogRepository to ApiCatalogRepository, backed by packages/api_client generated from the OpenAPI document.

The OpenAPI 3.1 document is the contract. It contains exactly one operation, the infrastructure health check GET /api/v1/health, because no story needs an API operation. It also defines the catalog component schemas (MockCatalog, Product, ProductVariant, ProductSummary, ProductPage, Money, LightingSpecifications, Error). These fix the exact JSON shape of the bundled mock catalog, which must validate against the MockCatalog schema, and of the future paginated list endpoint. The Prisma schema covers the catalog bounded area only, for when the NestJS backend is built. User, Cart, Order and Payment are deferred with their features.

Money is always an integer number of minor units (cents) plus an ISO 4217 code (USD only in M1). Formatting, tax and shipping use integer arithmetic only.

Flutter folder layout (feature-first):
- lib/main.dart
- lib/app.dart: MaterialApp.router with theme and router.
- lib/core/theme: design tokens (AppColors, AppTypography, AppSpacing, AppRadii, AppSizes including minTouchTarget 48) and ThemeData built from tokens.
- lib/core/router: app_router.dart with go_router config.
- lib/core/money: Money value type and formatMoney.
- lib/core/config: pricing_config.dart (kSalesTaxRateBasisPoints, kFlatShippingMinor = 999, kFreeShippingThresholdMinor = 15000, kLowStockThreshold = 5, kCatalogPageSize = 10).
- lib/core/widgets: AppNetworkOrAssetImage with placeholder and error fallback, PriceText with strike-through, StockStatusChip, LoadingView, EmptyView, ErrorView, CartBadgeButton.
- lib/features/catalog/data: mock_catalog_repository.dart and catalog_dto parsing.
- lib/features/catalog/domain: freezed models Product, ProductVariant, ProductSummary, ProductPage, LightingSpecifications, VariantOption, ProductImage, StockStatus; catalog_repository.dart interface.
- lib/features/catalog/presentation: product_list_screen.dart, product_detail_screen.dart, providers and widgets.
- lib/features/cart/domain: CartLine, CartTotals and the pure calculateCartTotals function.
- lib/features/cart/presentation: cart_screen.dart and cart_notifier.dart.
- test/: unit and widget tests.
- integration_test/: browse_to_cart_test.dart.
- assets/mock_catalog.json and assets/images/products/*.webp plus assets/images/placeholder.webp.

The Android debug build ships android/app/src/debug/res/xml/network_security_config.xml, which allows cleartext only for 10.0.2.2 so a future local staging API is reachable from the emulator. Release stays https-only.

Work item mapping:
- WI-001: project skeleton, theme tokens, router, core/money, core/config and network security configs.
- WI-002: domain models, MockCatalog JSON with 16 products and assets, MockCatalogRepository and parsing tests.
- WI-003: Product List screen.
- WI-004: Product Detail screen.
- WI-005: Cart.

The backend health module is not on the M1 critical path and must not delay any work item.

## Components
- **Flutter mobile app (lighting_shop)** (Flutter 3.x, Dart 3, flutter_riverpod (Notifier/AsyncNotifier), go_router, freezed, json_serializable): Single-codebase customer app, Android first. It hosts the three M1 screens (Product List, Product Detail, Cart), the theme built from design tokens, and go_router navigation. It makes no network calls in M1.
- **Bundled mock catalog** (JSON asset loaded with rootBundle.loadString, parsed with json_serializable into freezed models, bundled WebP images): Offline source of catalog data. assets/mock_catalog.json conforms exactly to the OpenAPI MockCatalog schema. It holds 16 products across the bulb, ceiling_light, pendant, lamp and smart_light types, including:
- at least one multi-variant product (finish plus color temperature)
- one product on sale
- one low-stock variant (stock 1 to 5)
- one fully out-of-stock product
- one variant with an intentionally missing image to exercise the error placeholder

Product and variant images are bundled under assets/images/products.
- **CatalogRepository (catalog data layer)** (Dart abstract class exposed via a Riverpod Provider<CatalogRepository>, overridable in tests): Abstract interface that isolates the UI from the data source. Methods:
- Future<ProductPage> fetchProducts({required int page, required int pageSize}): 1-based pages returning items (ProductSummary), total, page and pageSize.
- Future<Product> getProduct(String productId): throws ProductNotFoundException for unknown ids.

The M1 implementation, MockCatalogRepository, parses the asset once, caches it in memory and slices pages. A future ApiCatalogRepository will wrap the generated dart-dio client.
- **Money and pricing core** (Pure Dart in lib/core/money and lib/features/cart/domain, covered by flutter_test unit tests): Money value type {amountMinor: int, currency: String}. Two functions own all money rules:
- formatMoney(Money): integer-only formatting. dollars = amountMinor ~/ 100 with comma grouping, cents = (amountMinor % 100) padded to 2 digits, prefixed with $ for USD. Example: 12999 becomes $129.99.
- calculateCartTotals(lines, config): integer line totals, subtotal, tax rounded half-up in basis points, shipping and total.

Pricing constants live in lib/core/config/pricing_config.dart. No double is ever used for money.
- **In-memory cart store** (Riverpod Notifier<CartState> with a derived Provider<CartTotals> and Provider<int> for the badge count): Holds cart lines for the current app process only. Adds a variant with a quantity, merging with any existing line for the same variant. Clamps the quantity to 1..stockQuantity, updates quantity, removes lines and exposes a badge count. State is lost on app relaunch by design, and there is no checkout or payment entry point.
- **Router** (go_router): One route per screen spec:
- /products: ProductListScreen, the initial location.
- /products/:productId: ProductDetailScreen, a child route so the list stays in the navigator stack and keeps its scroll position.
- /cart: CartScreen, opened with context.push from the app bar cart badge on list and detail.

Unknown product ids render the detail error state.
- **Design system (theme tokens)** (Flutter ThemeData and ThemeExtension in lib/core/theme): Colors, typography, spacing, radii and sizes, chosen by the delivery team without approval. Colors meet WCAG AA contrast (4.5:1 for body text). Typography uses theme text styles so system font scaling is respected. AppSizes.minTouchTarget is 48. Widgets reference tokens only, with no hard-coded colors or sizes.
- **OpenAPI contract** (OpenAPI 3.1 YAML at docs/api/openapi.yaml, openapi-generator (dart-dio) when catalog endpoints are introduced): Source of truth for the API and the mock catalog JSON shape. M1 has one operation, getHealth. It also defines the component schemas for catalog models, pagination parameters, the shared Error schema and the bearerAuth scheme. It will later generate packages/api_client (dart-dio) and drive the NestJS DTOs.
- **NestJS API (deferred beyond health)** (NestJS, TypeScript, @nestjs/config, @nestjs/swagger, Prisma ORM, PostgreSQL 16, Docker/docker-compose): Future backend. M1 defines only the HealthModule: GET /api/v1/health returns 200 when PostgreSQL answers SELECT 1, otherwise 503 with the Error schema. It is not required by the M1 app and does not block any work item.
- **PostgreSQL catalog schema** (Prisma schema (prisma/schema.prisma), PostgreSQL 16): Relational model for Category, Product, ProductImage, ProductVariant, VariantOption and LightingSpecification, mirroring the OpenAPI catalog schemas. It is used once the catalog moves to the backend.
- **Android platform configuration** (Android Gradle, AndroidManifest.xml, res/xml/network_security_config.xml): Release manifest uses network_security_config with cleartextTrafficPermitted=false. The debug-only config in android/app/src/debug allows cleartext only for 10.0.2.2. There are no analytics or tracking SDKs.

## Backend modules
### health
Infrastructure readiness check. HealthController delegates to HealthService, which runs SELECT 1 through PrismaService.
- Returns 200 {status: ok, database: up, timestamp}.
- Returns 503 {statusCode, error, message} when the database is unreachable.

Public, with no auth guard. It exposes no versions, hostnames or connection details. It is the only backend operation in the M1 contract and is optional for the M1 app.
Entities: 

- `GET /api/v1/health`

### catalog (deferred, schema only)
Future owner of categories, products, variants, variant options and lighting specifications. In M1 it defines only the data model (Prisma) and the component schemas (OpenAPI) that the bundled mock catalog must match.

No catalog endpoints are part of the M1 contract, because the stories use the local catalog. When introduced, they will be the public paginated list and detail operations returning ProductPage and Product, using the existing Page and PageSize parameters.
Entities: Category, Product, ProductImage, ProductVariant, VariantOption, LightingSpecification


## Mobile app features
- catalog (US-001 Browse, US-002 Product detail and variants): screens ProductListScreen (route /products, initial location): paginated-style ListView.builder of ProductSummary rows. Each row shows:
- a lazily built image with loading placeholder and error placeholder
- name
- effective price formatted from cents
- the original price struck through when salePrice is set
- a StockStatusChip reading In stock, Low stock or Out of stock

The next page loads when the user scrolls within 3 rows of the end. It handles loading, empty ('No products available') and error (with Retry) states. Tapping a row calls context.go('/products/{id}'). The app bar has a cart badge., ProductDetailScreen (route /products/:productId, child of /products): shows the selected variant image, name, brand, the selected variant SKU, price and sale price, description, availability text and a Specifications section. The section lists only the non-null fields of the merged specifications (variant overrides on top of product specifications) with units: W, lm, K, V and mm.

Variant selectors are ChoiceChips grouped by option name (for example finish, color_temperature). The quantity stepper is bounded 1..stockQuantity. The Add to cart button is disabled and availability reads Out of stock when stockQuantity is 0. The screen handles loading, error and not-found states. Back returns to the list at the same scroll position. (state: Providers:
- catalogRepositoryProvider: Provider<CatalogRepository>, bound to MockCatalogRepository in M1 and overridden in tests.
- productListProvider: AsyncNotifier<ProductListState>. It holds items (List<ProductSummary>), total, the last loaded page, isLoadingMore and loadMoreError. build() loads page 1 with kCatalogPageSize = 10, loadNextPage() appends the next page until items.length == total, and refresh() reloads.
- productDetailProvider(productId): AsyncNotifierProvider.family returning Product.
- selectedVariantProvider(productId): NotifierProvider.family<String variantId>, initialised to the product's default variant (isDefault). select(optionName, value) resolves the variant whose options match the selected combination.
- selectedVariantViewProvider(productId): derived Provider exposing the price, sale price, image, SKU, stockQuantity, StockStatus and merged specifications of the current variant.
- detailQuantityProvider(productId): Notifier<int>, reset to 1 on variant change and clamped to 1..stockQuantity.

Stock status is derived in the domain layer: 0 is out_of_stock, 1..5 (kLowStockThreshold) is low_stock and above 5 is in_stock. For list rows, ProductSummary.stockStatus is computed from the sum of variant stock, and the price comes from the default variant.

Scroll position is preserved because the detail route is a child route (the list stays mounted beneath it) and the ListView uses a PageStorageKey.)
- cart (US-003, optional, dropped first if it delays M1): screens CartScreen (route /cart, opened via context.push from the app bar cart badge on list and detail): lists cart lines with image, product name, variant name, unit price and line total. Each line has a quantity stepper bounded 1..stockQuantity and a Remove action, all with 48dp targets and semantic labels. A summary section shows Subtotal, Tax, Shipping (or 'Free' when the subtotal is at least $150.00) and Total, all tax-exclusive. The empty state reads 'Your cart is empty' with a Browse products action. There is no checkout, sign-in or payment control. (state: cartProvider: NotifierProvider<CartNotifier, CartState>. CartState holds an ordered Map<String variantId, CartLine>. Each CartLine stores productId, variantId, productName, variantName, sku, unitPriceMinor (salePriceMinor ?? priceMinor at add time), currency, imageUrl, imageAltText, stockQuantity and quantity.

Methods:
- add(variantView, quantity): merges and clamps to stockQuantity, and rejects quantity < 1 or a stock of 0.
- setQuantity(variantId, q): clamps to 1..stockQuantity.
- remove(variantId).
- clear().

Derived providers:
- cartTotalsProvider: Provider<CartTotals> computed by the pure calculateCartTotals.
  - lineTotal = unitPriceMinor * quantity.
  - subtotal = sum of line totals.
  - tax = (subtotal * kSalesTaxRateBasisPoints + 5000) ~/ 10000, where kSalesTaxRateBasisPoints = 825 (8.25%, configurable constant); tax applies to merchandise only.
  - shipping = 0 if the cart is empty or subtotal >= 15000, otherwise 999.
  - total = subtotal + tax + shipping.
- cartItemCountProvider: Provider<int>, the sum of quantities, used for the badge.

The state is not persisted, so relaunching the app yields an empty cart.)

## Data model
Money:
- Every price is an integer number of minor units (cents) with an ISO 4217 currency code.
- OpenAPI: Money {amountMinor: integer >= 0, currency: 'USD'}.
- Prisma: price_minor INT, sale_price_minor INT NULL, currency CHAR(3) DEFAULT 'USD'.
- Dart: int with no double anywhere in the money path.
- salePrice, when present, is the price actually charged, and price is the original shown struck through. effectiveUnitPrice = salePrice ?? price.
- A raw SQL migration adds CHECK (price_minor >= 0), CHECK (sale_price_minor IS NULL OR (sale_price_minor >= 0 AND sale_price_minor < price_minor)), CHECK (stock_quantity >= 0) and CHECK (currency = 'USD') for the first release.

Variants:
- Stock, price, sale price, SKU and image live on ProductVariant, so stock checks and variant switching behave identically with the mock catalog and a future API.
- Every Product has at least one variant. Exactly one variant has isDefault = true, enforced by a partial unique index on product_variants(product_id) WHERE is_default in a raw SQL migration.
- The OpenAPI Product.defaultVariantId is derived from it.
- Variant options (for example finish=Matte Black, color_temperature=2700K) are ordered name/value pairs, unique per variant by name.
- The detail screen groups chips by option name and resolves the variant matching the selected combination. If no exact match exists, it picks the first variant matching the changed option.
- SKU is globally unique.

Stock status:
- It is derived, never stored: 0 is out_of_stock, 1..5 is low_stock and above 5 is in_stock.
- The product-level status used in list rows is computed from the sum of variant stock.
- There is no reservation or release in M1, since there is no checkout. The future checkout reserves per variant as per project rules.

Lighting specifications:
- They form a typed object with nullable fields: wattageW, lumens, colorTemperatureK, dimmable, bulbType, baseType, voltageV, material, finish, widthMm, heightMm, depthMm and ipRating.
- A null or absent field means not applicable and is not rendered. This is how the detail screen shows only the specifications relevant to the product type: a bulb carries wattage, lumens, color temperature, dimmable and bulb type, while a fixture carries material, finish, dimensions and IP rating.
- A product has one base specification. A variant may have a specificationOverrides object whose non-null fields replace the base values, for example when a wattage or colorTemperature variant changes those fields.
- In PostgreSQL both are rows in lighting_specifications, linked 1:1 (optional) from products.specification_id and product_variants.specification_override_id.
- Dimensions are integer millimetres, power is integer watts, voltage is integer volts and color temperature is integer kelvin.

Images:
- Each image has a url plus a required altText, used as the Semantics label.
- In M1 the url is a bundled asset path (for example assets/images/products/pendant-aria-black.webp). Later it is an https URL.
- A missing or broken image shows the placeholder asset.

Rating:
- ratingAverage (0.0 to 5.0, one decimal, nullable when ratingCount is 0) and ratingCount are display-only. This is not money, so a decimal is acceptable.

Pagination:
- List responses are ProductPage {items, total, page, pageSize}, with a 1-based page and pageSize 1..100 (default 20; the app uses 10).
- MockCatalogRepository applies the same slicing, so switching to the API needs no UI change.

Identifiers:
- ids are strings. They are UUIDs in PostgreSQL, while the mock uses stable readable ids such as prd_001 and var_001_a.

Cart:
- The M1 cart is an in-memory client structure only, with no Cart or CartItem tables.
- Cart lines snapshot product name and unit price at add time, matching the future order-line copy rule.

Deferred entities:
- User, Address, Cart, CartItem, Order, OrderItem and Payment are deferred to the releases that add auth, persistent carts, checkout and Stripe.
- They will follow the project rules: order status pending_payment -> paid -> fulfilled -> delivered plus cancelled and refunded, order lines copying name and unit price, bcrypt or argon2 password hashes, and account deletion.

Mock catalog file:
- assets/mock_catalog.json is {catalogVersion: 1, products: Product[]} and must validate against components.schemas.MockCatalog.
- A unit test asserts the required fixtures exist: a multi-variant product, a sale, low stock and out of stock.

## Security
- M1 handles no authentication, no personal data and no payment data. No card data can be entered, stored or transmitted, and no sign-in, checkout or payment UI exists.
- The M1 app makes no network requests. The catalog and images are bundled assets, so the app runs offline and there is no remote attack surface.
- Release builds are https-only. network_security_config sets cleartextTrafficPermitted=false. The debug-only config under android/app/src/debug/res/xml allows cleartext solely for 10.0.2.2 to reach local staging from the emulator, and it is never merged into release.
- No analytics, crash-reporting or tracking SDKs are included, so no consent prompt is needed. New dependencies are limited to flutter_riverpod, go_router, freezed_annotation and json_annotation (plus build_runner, freezed and json_serializable as dev dependencies) and are reviewed before addition.
- Parsing of the bundled catalog is defensive. The JSON is validated against the domain models at load time. A malformed file surfaces the list error state instead of crashing, and broken image references fall back to the placeholder via errorBuilder.
- Money integrity: integer minor units and integer-only tax rounding (half-up in basis points) eliminate floating-point rounding errors. Cart quantities are clamped to 1..stockQuantity in the Notifier, not only in the UI.
- Contract readiness for later releases: the OpenAPI document defines a bearerAuth (JWT) scheme applied globally. Only public operations such as getHealth opt out with security: []. Access tokens (15 min) and refresh tokens will be stored with flutter_secure_storage.
- The health endpoint is public but minimal. It returns only status, database and timestamp and never exposes versions, hostnames, stack traces or connection strings. Errors use the shared {statusCode, error, message} shape.
- Backend configuration (for the health module and later modules) comes from environment variables validated at startup with @nestjs/config (for example DATABASE_URL and PORT). No secrets are committed, and .env files are gitignored.
- Future backend hardening, planned but not in M1: a global ValidationPipe with whitelist and forbidNonWhitelisted, helmet, a CORS allow-list, rate limiting on auth endpoints, bcrypt or argon2 password hashing, account deletion, and Stripe PaymentIntents confirmed by the SDK with webhook signature verification.

## Architecture decisions
### ADR-001: Bundled mock catalog behind a CatalogRepository interface instead of a backend in M1
**Context:** The speed demo must launch on an Android emulator immediately, offline, with no backend, and render the first list within 3 seconds. The roadmap still requires a NestJS catalog API later, and the list must be pagination-ready.

**Decision:** Ship assets/mock_catalog.json, conforming to the OpenAPI MockCatalog schema, plus bundled images. Access it only through an abstract CatalogRepository with fetchProducts(page, pageSize) -> ProductPage and getProduct(id). Bind it to MockCatalogRepository through a Riverpod provider. The asset is parsed once and cached in memory. The list screen consumes pages (pageSize 10) with infinite scroll, even though all data is local.

**Consequences:** The app starts coding and runs from WI-001 with no infrastructure. Replacing the data source later means adding ApiCatalogRepository and changing one provider binding. Screens, providers and tests are unchanged. The mock JSON must be kept valid against the contract schema, enforced by a unit test. There is no live stock or pricing, which is acceptable for the demo.

### ADR-002: Integer minor-unit money with integer-only formatting, tax and shipping arithmetic
**Context:** Project rules forbid floating-point money. The PRD requires USD display from cents (12999 -> $129.99), a flat configurable tax rate, $9.99 shipping and free shipping at $150.00 or more.

**Decision:** Represent money as Money {amountMinor: int, currency: 'USD'} everywhere: JSON, OpenAPI, Prisma INT columns and Dart int. formatMoney uses ~/ and % with manual thousands grouping and never converts to double. Pricing rules live in lib/core/config/pricing_config.dart:
- The tax rate is kSalesTaxRateBasisPoints = 825.
- tax = (subtotal * bps + 5000) ~/ 10000, rounding half-up.
- Shipping is 999 below a subtotal of 15000, otherwise 0, and 0 for an empty cart.
- Tax applies to merchandise only.
- Prices are displayed tax-exclusive.

**Consequences:** Totals are exact and deterministic, and the threshold edge cases (14999 vs 15000) and tax rounding are straightforward to unit test. intl currency formatting is not used, because it takes doubles. Multi-currency would require per-currency minor-unit exponents, which is out of scope for this release.

### ADR-003: In-memory cart as a Riverpod Notifier with price snapshots and stock clamping
**Context:** US-003 is optional and must not delay the must-have stories. The cart must reset on relaunch, must not exceed variant stock, and must not offer checkout. Future carts will be server-side and tied to a signed-in user.

**Decision:** Implement CartNotifier (Notifier<CartState>) keyed by variantId. It copies product name, variant name, SKU, image and effective unit price at add time, and enforces 1 <= quantity <= stockQuantity inside the Notifier. Totals come from a pure calculateCartTotals function exposed through a derived provider. There is no persistence layer.

**Consequences:** The cart is simple, fully testable without Flutter bindings, and trivially dropped if time runs short, since the detail screen's Add to cart button is the only coupling. The snapshot mirrors the future order-line copy rule. When server carts arrive, the Notifier's state source changes to the API while its public methods can stay the same.

### ADR-004: Contract-first OpenAPI with only the health operation; catalog shapes defined as component schemas
**Context:** Scope allows at most 4 API operations and says only endpoints the stories need. The stories need none because the catalog is local, but the health check must be in the contract. Developers need an exact data shape so the mock can later be replaced by a generated client.

**Decision:** The OpenAPI 3.1 document contains one operation, getHealth (GET /health under server base /api/v1). It also contains the component schemas MockCatalog, Product, ProductVariant, ProductSummary, ProductPage, Money, LightingSpecifications, VariantOption, Image, Category, StockStatus, ProductType and Error, the Page and PageSize parameters and the bearerAuth scheme. In M1 the Flutter domain models are hand-written freezed classes mirroring these schemas field-for-field. packages/api_client (dart-dio) is generated from the same document as soon as the first catalog endpoint is added.

**Consequences:** The contract stays within scope and still pins down the data model, so there is no guessing when the backend arrives. Until then the 'HTTP only through the generated client' rule is satisfied trivially, because there is no HTTP. The team must regenerate the client and delete or replace the hand-written models in the release that introduces catalog endpoints.

### ADR-005: go_router with the detail screen as a child route of the list to preserve scroll position
**Context:** US-002 requires the back control to return to the product list at the same scroll position. The convention is one route per screen spec with go_router.

**Decision:** Define three routes:
- /products, the initial location.
- /products/:productId, a child GoRoute of /products.
- /cart, top-level and opened with context.push.

The list uses ListView.builder with a PageStorageKey. Its paging state lives in productListProvider, which is not autoDispose, so it survives while the detail screen is on top.

**Consequences:** The list widget stays in the navigator stack under the detail screen, so offset and loaded pages are preserved, and the Android system back works. The paths already match the future REST resource naming, and adding auth redirects later is a router-level change.

### ADR-006: Typed nullable lighting specifications with variant-level overrides
**Context:** The detail screen must show only specifications applicable to the product type: wattage, lumens, color temperature, dimmable and bulb type for bulbs; material, finish, dimensions and IP rating for fixtures. Some variants change specification values such as wattage or color temperature. A free-form key/value map would weaken validation and comparison for project buyers.

**Decision:** Use one LightingSpecifications object with fixed, typed, nullable fields, with integer units (W, lm, K, V, mm) and ipRating matching ^IP[0-9X]{2}$. The product has base specifications, and a variant may carry specificationOverrides. The UI merges them, overrides winning where non-null, and renders only non-null fields in a fixed, localized order.

**Consequences:** Specifications are validated, comparable and consistently formatted, and the 'only applicable' rule is data-driven with no per-type UI branching. Adding a new specification requires a contract, model and migration change, which is intentional and reviewable.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.