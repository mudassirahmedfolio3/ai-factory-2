# Architecture

Speed-demo architecture for the Lighting E-Commerce Android app (M1: Browse-to-Cart Journey). M1 delivers a single, fully offline Flutter 3.x app with three screens: Product List, Product Detail and an in-memory Cart. It uses Riverpod, go_router and freezed. There is no backend, no authentication, no payments and no network calls in M1.

The catalog is a hand-written JSON asset of 12 lighting products bundled in the app. It is loaded through a CatalogRepository interface, implemented by MockCatalogRepository. The asset's shape mirrors the ProductSummary and ProductDetail schemas of the OpenAPI contract in this document. In a later milestone, an ApiCatalogRepository backed by the generated dart-dio client (packages/api_client) replaces the mock without touching presentation or cart code.

The OpenAPI 3.1 contract and Prisma schema are therefore forward-looking but exact. They cover only the read-only catalog (listProducts, getProduct) plus the health check, which are the only server operations the must-have stories would need. They are the contract for the future NestJS catalog and health modules. They are not built in M1.

Money is always integer minor units (pence) plus an ISO 4217 code (GBP). Prices include 20% VAT. Formatting to £ happens only in the presentation layer, via integer arithmetic.

Stock status is derived from stockQuantity with one global low-stock threshold of 5:
- 0 -> out_of_stock
- 1..5 -> low_stock
- more than 5 -> in_stock

The cart is a keep-alive Riverpod Notifier held in memory. It is intentionally lost on app restart.

## Components
- **Flutter mobile app (lighting_shop)** (Flutter 3.x, Dart 3, flutter_riverpod (Notifier/AsyncNotifier), go_router, freezed + json_serializable, intl): Android-first shopper app with three routes: '/' Product List, '/products/:productId' Product Detail and '/cart' Cart. Uses feature-first folders lib/features/{catalog,cart}/{data,domain,presentation}. Shared code lives in lib/core (theme, router, money formatting, widgets). Makes no network calls in M1.
- **Bundled mock catalog asset** (JSON asset declared in pubspec.yaml; WebP placeholder images (max 800px wide)): Hand-written seed of 12 lighting products across 7 categories: ceiling lights, pendants, wall lights, table and floor lamps, bulbs, outdoor, and smart lighting. It is stored at assets/catalog/products.json with placeholder images at assets/images/products/*.webp. The seed must include at least 2 sale items, 2 low-stock items (1-5 units) and 1 out-of-stock item. The JSON shape equals the OpenAPI ProductDetail schema, with imageUrl holding an asset path such as 'asset://images/products/pendant-01.webp'.
- **CatalogRepository (domain interface) + MockCatalogRepository (data)** (Dart abstract class; Riverpod Provider<CatalogRepository> so tests and a future ApiCatalogRepository can override it): Abstraction for catalog reads with two methods:
- listProducts({page, pageSize}) -> ProductPage
- getProduct(productId) -> ProductDetail, throwing ProductNotFoundException when the id is unknown.

The mock loads and parses the asset once via rootBundle, caches the result, and sorts by name ascending then id. It paginates in memory with the same semantics as the API (page from 1, pageSize 1-100, default 20).

It validates seed invariants on load and throws CatalogDataException if any fails:
- priceMinor > 0
- salePriceMinor < priceMinor when present
- stockQuantity >= 0
- currency == 'GBP'
- **Core: money, theme, router, widgets** (Dart, intl, Material 3): lib/core/money holds a Money value object (int amountMinor, String currency) and formatGbp(int pence). Formatting uses integer division and remainder, with intl NumberFormat applied to the integer pounds part only for grouping. Output looks like '£1,234.50'; no doubles are used.

lib/core/theme holds agent-chosen design tokens (AppColors, AppTypography, AppSpacing, AppRadii) and a ThemeData that is WCAG AA compliant.

lib/core/router holds the GoRouter configuration.

lib/core/widgets holds shared widgets: PriceText (handles strike-through for sale prices), StockBadge, LoadingView, EmptyView, ErrorView (with retry), and CartBadgeButton.
- **Future: NestJS API (not built in M1)** (NestJS (TypeScript), @nestjs/swagger, @nestjs/config, class-validator, Prisma ORM): Implements the OpenAPI contract in this document when backend work begins. Global prefix /api/v1. Contains the catalog and health modules for this contract. The auth, users, cart, orders and payments modules are added in later milestones.
- **Future: PostgreSQL database (not built in M1)** (PostgreSQL 16, Prisma migrations): Stores categories, products and product specifications per the Prisma schema in this document.
- **Future: packages/api_client (not generated in M1)** (openapi-generator dart-dio): dart-dio client generated from openapi_yaml, via the operationIds getHealth, listProducts and getProduct. It will back ApiCatalogRepository. No endpoint is ever hand-written.

## Backend modules
### catalog (deferred - not built in M1)
Public, read-only product catalog. Only active products are returned.

List behaviour:
- Paginated with page and pageSize.
- Ordered by name ascending, then id ascending.

For every product the module:
- Derives stockStatus using the global LOW_STOCK_THRESHOLD=5.
- Returns prices as integer minor units with the currency code.
- Returns specifications with non-applicable (null) fields omitted.

The controller is thin; CatalogService does the work through PrismaService.
Entities: Category, Product, ProductSpecification

- `GET /api/v1/products`
- `GET /api/v1/products/{productId}`

### health (deferred - not built in M1)
Liveness plus database reachability. Runs SELECT 1 via PrismaService. Returns 200 {status:'ok', database:'up'} or 503 with the shared error schema.
Entities: 

- `GET /api/v1/health`

## Mobile app features
- catalog: screens ProductListScreen (route '/', name 'productList'), ProductDetailScreen (route '/products/:productId', name 'productDetail') (state: Providers:
- catalogRepositoryProvider: Provider<CatalogRepository>, defaulting to MockCatalogRepository.
- productListProvider: AsyncNotifier<ProductPage>, which loads page 1 with pageSize 50. The whole seed fits on one page; the provider exposes a loadMore stub for the API later.
- productDetailProvider: AsyncNotifierProvider.family<ProductDetail, String> keyed by productId.

Every screen renders AsyncValue with LoadingView, EmptyView ('No products available') and ErrorView (with retry that invalidates the provider). An unknown productId shows 'Product not found'.

Product List screen:
- ListView.builder with a PageStorageKey, so scroll position is kept.
- Detail is opened with context.pushNamed, so back returns to the same scroll position.
- Images use Image.asset with cacheWidth, so only visible rows decode (lazy).
- Each card is an InkWell of at least 48dp with a Semantics label combining name, price and stock status.

Product Detail screen:
- Quantity selector state is local (a StateProvider.autoDispose.family keyed by productId), ranging from 1 to stockQuantity.
- Add to cart is disabled when stockStatus == out_of_stock.
- The specifications section renders only non-null spec fields as label/value rows, in a fixed order.)
- cart: screens CartScreen (route '/cart', name 'cart') (state: cartProvider is a keepAlive NotifierProvider<CartNotifier, CartState>. CartState is a freezed model: List<CartLine> lines, with derived getters itemCount (sum of quantities) and subtotalMinor (sum of lineTotalMinor).

CartLine (freezed) has these fields: productId, name, imageUrl, imageAlt, unitPriceMinor (the sale price if present, else the price), currency, maxQuantity (stockQuantity snapshot), quantity. It has the getter lineTotalMinor = unitPriceMinor * quantity (int).

CartNotifier methods:
- add(ProductDetail, int qty): merges with an existing line.
- setQuantity(productId, int qty)
- remove(productId)
- clear()

add and setQuantity cap the quantity at maxQuantity and return a CartUpdateResult {capped: bool, appliedQuantity}. The UI uses it to show a SnackBar: 'Only N in stock - quantity limited to N'. Adding to cart also shows a confirmation SnackBar.

CartBadgeButton in the app bars of the list and detail screens watches cartProvider.select((s) => s.itemCount).

The Cart screen shows an empty state message when there are no lines. The cart is memory only and is not persisted, so a relaunch starts with an empty cart.)

## Data model
1. Money: every price is an integer number of minor units (pence) plus a 3-letter ISO 4217 currency code. The only currency in scope is GBP. Fields are priceMinor, salePriceMinor (nullable) and currency. Prices include 20% VAT; there is no VAT breakdown in M1. Floats are never used: Dart uses int, Prisma uses Int, and OpenAPI uses integer. Display formatting splits pence into pounds = pence ~/ 100 and pennies = pence % 100, padded to 2 digits.

2. Effective price = salePriceMinor ?? priceMinor. Invariants:
- priceMinor > 0
- 0 < salePriceMinor < priceMinor when present
- stockQuantity >= 0
They are validated by the mock repository on load and, later, by SQL CHECK constraints. Prisma cannot express CHECK constraints, so they are added in the first migration's raw SQL:
- CHECK ("priceMinor" > 0)
- CHECK ("salePriceMinor" IS NULL OR ("salePriceMinor" > 0 AND "salePriceMinor" < "priceMinor"))
- CHECK ("stockQuantity" >= 0)
- CHECK (currency ~ '^[A-Z]{3}$')

3. Stock is tracked per product in this milestone, because variants are explicitly out of scope in the PRD (see ADR-005). stockStatus is derived, never stored: 0 = out_of_stock, 1-5 = low_stock, >5 = in_stock. The UI labels are 'Out of stock', 'Low stock' and 'In stock'.

4. Lighting specifications are a typed, fixed set of optional fields rather than a free-form map, so labels, units and ordering are deterministic:
- wattageW, lumens, colorTemperatureK, voltageV, lightType, dimmable, material, finish
- dimensionsMm {widthMm, heightMm, depthMm, diameterMm}
- weightG, ipRating (e.g. 'IP44'), bulbType (e.g. 'E27', 'GU10'), bulbIncluded
Non-applicable fields are omitted in JSON (null in the database) and are not rendered.

Display labels and units in order:

| Field | Label | Display |
|---|---|---|
| wattageW | Wattage | 'N W' |
| lumens | Lumens | 'N lm' |
| colorTemperatureK | Colour temperature | 'N K' |
| voltageV | Voltage | 'N V' |
| lightType | Light type | text |
| dimmable | Dimmable | Yes/No |
| material | Material | text |
| finish | Finish | text |
| dimensionsMm | Dimensions | 'W x H x D mm' or 'Ø D mm' |
| weightG | Weight | 'N g', or 'N.N kg' when >= 1000 via integer math |
| ipRating | IP rating | text |
| bulbType | Bulb type | text |
| bulbIncluded | Bulb included | Yes/No |

5. Identifiers: UUID v4 strings. The mock seed uses fixed UUIDs so tests are deterministic. SKU is unique, uppercase, e.g. 'LUX-PEN-001'.

6. imageUrl: in the API it is an absolute https URL. In the mock it is an 'asset://' URI resolved to an asset path by the data layer. imageAlt is a required non-empty semantic label.

7. Categories are a flat list (id, slug, name, sortOrder). Category navigation is out of scope, but category is shown on cards and detail.

8. Domain entities deferred to later milestones: User, Address, Cart and CartItem (server side), Order, OrderItem, Payment, ProductVariant. They are intentionally absent from the Prisma schema.

9. The Dart domain models (freezed + json_serializable) are ProductSummary, ProductDetail, Category, LightingSpecifications, Dimensions, ProductPage and StockStatus (an enum with JsonValue 'in_stock'/'low_stock'/'out_of_stock'). Their field names are exactly those in the OpenAPI schemas.

## Security
- M1 makes no network calls, has no authentication, and collects or stores no personal or payment data. The catalog is read-only public data bundled in the APK.
- The release AndroidManifest (android/app/src/main) declares no INTERNET permission in M1; Flutter adds INTERNET only in the debug/profile manifests for tooling. The release build has no cleartext traffic permitted: usesCleartextTraffic=false and there is no main network security config allowing cleartext.
- A debug-only network security config (android/app/src/debug/res/xml/network_security_config.xml, referenced from the debug manifest) permits cleartext for the domain 10.0.2.2 only, so future debug builds can reach local staging at http://10.0.2.2:3000. Release stays https-only.
- The cart lives only in process memory (Riverpod state). Nothing is written to disk, shared preferences or secure storage. flutter_secure_storage is not added until auth arrives.
- The mock catalog is validated on load (price, sale price, stock and currency invariants). Malformed data surfaces as the ErrorView and never crashes the app or yields wrong totals.
- Quantity inputs are clamped to 1..stockQuantity in CartNotifier (a single source of truth), not only in the widget.
- No secrets, keys or endpoints are hard-coded. The future API base URL comes from --dart-define (API_BASE_URL) and is validated at startup.
- Future API (when built): catalog and health endpoints are public (security: [] override); a bearerAuth JWT scheme is declared globally for later protected modules.
- Future API: request validation is done by class-validator DTOs with whitelist and forbidNonWhitelisted. Query params page and pageSize are range-checked. productId is validated as a UUID; an invalid value returns 400.
- Future API: errors use { statusCode, error, message } with no stack traces. Additional protections are helmet, rate limiting via @nestjs/throttler (e.g. 100 req/min/IP on public reads), and config validated with @nestjs/config + Joi. DATABASE_URL comes from the environment only, and the database user has least privilege.
- Dependency hygiene: pin Flutter packages in pubspec.lock, run flutter analyze and flutter test in GitHub Actions, and enable Dependabot for pub.

## Architecture decisions
### ADR-001: Bundled mock catalog behind a CatalogRepository interface for M1
**Context:** The speed demo must run on an Android emulator immediately, with no backend, account or network. Scope forbids backend work in M1. At the same time, the app will later consume a real NestJS catalog API through a generated client.

**Decision:** Ship the catalog as a JSON asset (assets/catalog/products.json) whose shape exactly equals the OpenAPI ProductDetail schema. Load it through MockCatalogRepository, which implements the domain interface CatalogRepository with the same pagination and not-found semantics as the API contract. Presentation and cart code depend only on the interface, via catalogRepositoryProvider.

**Consequences:** Positive:
- Zero-setup offline demo.
- Deterministic data for widget tests.
- The later switch to the API is a provider override plus a thin mapper from generated api_client models to domain models.

Negative:
- Stock in the demo is static and not shared between devices.
- Contract drift between the asset and the OpenAPI document must be guarded by a unit test that parses the asset into the domain models and asserts the seed invariants.

### ADR-002: Define the catalog API contract now, implement it later
**Context:** The team designs contract-first, and the app's domain models should not need renaming when the backend arrives. However, the scope limits server work in M1 to none and API operations to at most 4.

**Decision:** Publish an OpenAPI 3.1 contract with only getHealth, listProducts and getProduct (2 business operations plus health). Provide the matching Prisma schema (Category, Product, ProductSpecification). Neither is implemented in M1. The Dart domain models use the exact schema field names. The api_client package is generated only when the backend milestone starts.

**Consequences:** Positive:
- Developers have an exact target.
- The mock and future API cannot silently diverge.

Negative:
- Some documentation is written ahead of code. If PRD changes (e.g. variants) occur, the contract version must be bumped (info.version 0.x signals instability).

### ADR-003: Money as integer minor units with currency, formatted via integer arithmetic
**Context:** Project rules forbid floats for money. The PRD requires GBP prices in pence, including 20% VAT, with sale prices and cart subtotals.

**Decision:** All prices are int pence plus a currency code: priceMinor, salePriceMinor and currency in the contract, database and Dart models. Cart line totals and subtotals are int multiplication and sums. A single core function formatMoney(int minor, String currency) renders '£1,234.50' by splitting into pounds and pennies with ~/ and %. Only the integer pounds part is passed to intl for thousands grouping. Unit tests cover:
- 0
- 5
- 99
- 100
- 123456
- sale versus original price
- subtotal sums

**Consequences:** Positive:
- No rounding errors.
- Straightforward to extend to VAT breakdown later, using integer division with explicit rounding rules.

Negative:
- Multi-currency formatting would need per-currency exponent handling, which is out of scope.

### ADR-004: In-memory cart as a keep-alive Riverpod Notifier
**Context:** US-003 needs a cart whose count and subtotal update immediately across screens, with no persistence. The cart must be empty after relaunch, and guest carts on the server are out of scope.

**Decision:** Use a keepAlive NotifierProvider<CartNotifier, CartState> with immutable freezed state. CartLine snapshots name, effective unit price and stock (maxQuantity) at add time. CartNotifier enforces quantity clamping to 1..maxQuantity and returns whether capping occurred, so the UI can explain the limit.

**Consequences:** Positive:
- Simple and testable pure logic (unit tests without widgets).
- Badges rebuild via select.

Negative:
- State is lost on process death, which is the desired behaviour.
- When a server cart arrives, CartNotifier becomes an AsyncNotifier backed by a CartRepository, and snapshot prices must be re-validated server-side.

### ADR-005: Stock tracked per product in this milestone; variants deferred
**Context:** The project convention tracks stock per product variant. The approved PRD explicitly puts product variants and variant-level inventory out of scope, and the mock data model lists stock quantity on the product.

**Decision:** For M1 and this contract, stockQuantity lives on Product and stockStatus is derived with a global threshold of 5. When variants are introduced, a ProductVariant table will take over sku, price, salePrice and stockQuantity. The migration will create one default variant per existing product, and the API will add a variants array to ProductDetail in a new contract version.

**Consequences:** Positive:
- Matches the PRD exactly.
- Minimal model.

Negative:
- A planned breaking migration when variants arrive. Checkout stock reservation is also deferred until then, since there is no checkout in M1.

### ADR-006: Typed lighting specifications instead of a free-form key/value map
**Context:** The PRD describes a 'map of lighting specifications'. The detail screen must show label/value pairs, and must hide specifications that are not applicable. Free-form maps lead to inconsistent keys, units and labels.

**Decision:** Model specifications as a fixed optional-field object: LightingSpecifications in OpenAPI and freezed, and a 1:1 ProductSpecification table in Prisma. Units are encoded in the field names (W, lm, K, V, mm, g), and there are enumerated display labels and order. Null or absent fields are not rendered.

**Consequences:** Positive:
- Deterministic rendering and validation.
- Values are queryable later for filters.

Negative:
- A new spec type requires a schema change and migration. This is acceptable for a small, stable lighting attribute set.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.