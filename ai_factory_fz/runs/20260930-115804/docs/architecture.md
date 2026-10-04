# Architecture

beauty-mini M1 is a Flutter-only speed demo that runs on an Android emulator with a plain `flutter run` right after scaffold. It has no backend, no network calls, no auth, no payments and no checkout. The app bundles a hard-coded catalog of exactly 8 beauty products: lipstick, foundation, mascara, face serum, moisturizer, perfume, nail polish and makeup brush set. Each product has an integer price in cents with currency USD, a short description and a placeholder color token instead of an image.

The app has 2 screens, which is within the 3-screen limit:
- Browse (`/`): a 2-column product grid with a cart count badge in the app bar.
- Product detail (`/products/:productId`): name, price, description and an Add to cart button.

The cart is an in-memory Riverpod Notifier that counts total items added. It resets on app restart and has no cart screen, quantities or removal.

The code follows the project's Flutter conventions so later milestones can extend it without restructuring:
- Feature-first folders (`lib/features/<feature>/{data,domain,presentation}`, with shared code in `lib/core`).
- Riverpod for state, go_router for navigation, and theme design tokens in `lib/core/theme`.

The catalog sits behind a repository interface (`CatalogRepository`). In M1 it is implemented by `LocalCatalogRepository`. In a later milestone it can be swapped for an implementation backed by the generated OpenAPI client (`packages/api_client`, dart-dio) without touching the presentation layer.

To keep setup under 10 minutes, the app adds only `flutter_riverpod` and `go_router`. There is no code generation (no freezed/json_serializable/build_runner) and no dio or api_client in M1.

The OpenAPI 3.1 contract and Prisma schema are deliberately minimal and forward-looking:
- The contract defines zero business operations, because the stories need none. It contains only the infrastructure health check (`GET /api/v1/health`), the shared Error schema, the bearer auth scheme, the pagination envelope, and the Product/Money schemas that mirror the local Dart model. This fixes the future shape.
- The Prisma schema defines only the future Product catalog table.
- Neither is deployed or implemented in M1. No NestJS service or /health endpoint is built in this milestone, per the PRD.

## Components
- **beauty_mini Flutter app (Android)** (Flutter 3.x (Dart 3), Material 3, flutter_riverpod, go_router; Android first): The only runnable component in M1. It renders the browse grid and product detail screens, holds the in-memory cart count, and formats prices from integer cents. It runs fully offline on an Android emulator with `flutter run` and no configuration.
- **Core: theme / design tokens (lib/core/theme)** (Dart ThemeData + ThemeExtension (AppTokens, PlaceholderPalette)): Single source of colors, the placeholder color palette, typography, spacing, radii and minimum touch target (48dp). Widgets never hard-code colors or sizes. The team chose the tokens without an approval step.
- **Core: router (lib/core/router)** (go_router): Declares one GoRoute per screen spec: `/` for Browse and `/products/:productId` for Product detail. It handles unknown product ids with a not-found state and supports system back navigation.
- **Core: money formatting (lib/core/money)** (Pure Dart utility with unit tests): Formats integer minor units plus an ISO 4217 code for display, for example 1999 USD is shown as $19.99. It uses integer arithmetic only (~/ and %) and never converts to double.
- **Catalog feature (lib/features/catalog)** (Dart, flutter_riverpod): Product domain model, the CatalogRepository interface, LocalCatalogRepository with the 8 bundled products, Riverpod providers, and the Browse and Product detail screens.
- **Cart feature (lib/features/cart)** (flutter_riverpod Notifier): In-memory CartNotifier that counts total items added, the CartBadge app bar widget, and the AddToCartButton. It has no persistence, no cart screen, no quantities and no removal.
- **Tests (test/, integration_test/)** (flutter_test, integration_test): Widget tests:
- Browse: 8 tiles, names, formatted prices, semantics.
- Detail: matching name and price, back navigation.
- Cart badge: hidden at 0, increments per tap.
Also unit tests for money formatting and the catalog, plus one integration_test for the browse -> detail -> add to cart -> back -> badge = 1 journey.
- **API contract (docs/openapi.yaml) - contract only, not deployed in M1** (OpenAPI 3.1 YAML): Forward-looking OpenAPI 3.1 contract. It contains only the health check plus shared schemas (Error, Money, Product, pagination) that mirror the local model, so a later backend and the generated dart-dio client match the M1 data shape. No server implements it in M1.
- **Database schema (prisma/schema.prisma) - design only, not deployed in M1** (Prisma ORM, PostgreSQL 16): Forward-looking Prisma schema for the future catalog (Product) matching the local model. It is not migrated or run in M1.

## Backend modules
### health (deferred - contract only, not implemented in M1)
Future NestJS HealthModule. GET /api/v1/health returns 200 when the database is reachable and 503 otherwise. Per the PRD, no backend and no /health endpoint are built in M1. This entry only reserves the contract so the first backend milestone starts from it.
Entities: 

- `GET /api/v1/health`

## Mobile app features
- catalog: screens BrowseScreen (route '/', name 'browse')
- AppBar titled 'beauty-mini' with CartBadge.
- GridView with 2 columns showing exactly 8 ProductTile widgets.
- Each tile shows a placeholder color block from a PlaceholderPalette token, the product name and the price formatted from cents.
- Each tile is wrapped in InkWell/Semantics(button: true, label: '<name>, <price>') with at least a 48dp tap target.
- Tapping a tile calls context.push('/products/<id>').
- States: empty ('No products yet' message), error (message + Retry that invalidates productsProvider), loading (spinner, practically unseen because data is synchronous)., ProductDetailScreen (route '/products/:productId', name 'productDetail')
- AppBar with back button.
- Large placeholder color block with semantic label '<name> placeholder image', then name, USD price, short description and AddToCartButton.
- System back / AppBar back pops to Browse, and the grid state is preserved because push is used.
- States: not-found/error when productId is unknown ('Product not found' + 'Back to products' button); loading spinner for API parity. (state: Riverpod (flutter_riverpod, no codegen).

Providers:
- catalogRepositoryProvider = Provider<CatalogRepository>((ref) => const LocalCatalogRepository()).
- productsProvider = Provider<List<Product>>((ref) => ref.watch(catalogRepositoryProvider).listProducts()).
- productByIdProvider = Provider.family<Product?, String>((ref, id) => ref.watch(catalogRepositoryProvider).findById(id)).

The data is synchronous and immutable in M1, so plain Providers are used. When the API arrives, these become AsyncNotifier/FutureProvider with no screen restructuring, because the screens already render loading/empty/error branches.

Folders:
- lib/features/catalog/domain/product.dart: immutable Product class with id, name, description, priceCents (int), currency ('USD'), placeholderColor (PlaceholderColor enum token).
- lib/features/catalog/data/local_catalog_repository.dart.
- lib/features/catalog/presentation/{browse_screen.dart, product_detail_screen.dart, widgets/product_tile.dart}.)
- cart: screens No dedicated screen. A cart contents screen is out of scope., CartBadge widget in the BrowseScreen AppBar: a cart icon with semantic label 'Cart, N items' inside a Badge.
- Hidden when count == 0.
- Shows N when count > 0.
- Not tappable, and no checkout exists anywhere., AddToCartButton on ProductDetailScreen: FilledButton 'Add to cart' with a minimum size of 48dp.
- Each tap calls cartProvider.notifier.add(productId).
- Shows a SnackBar 'Added to cart'. (state: Riverpod Notifier.

cartProvider = NotifierProvider<CartNotifier, CartState>.
- CartState is an immutable object holding List<String> productIds (one entry per tap) and exposes int get count => productIds.length.
- CartNotifier.build() returns an empty CartState.
- add(String productId) appends the id.

The ProviderScope lives at the app root, so the state survives navigation between Browse and Detail. It lives only in memory and resets on app restart. There are no persistence packages.

Folders:
- lib/features/cart/domain/cart_state.dart
- lib/features/cart/presentation/{cart_notifier.dart, widgets/cart_badge.dart, widgets/add_to_cart_button.dart}

The feature is priority 'could'. If it slows delivery it is cut by removing the badge and button, with no impact on the catalog feature.)

## Data model
M1 runtime data model (Dart, bundled in the app, no database). The Product fields are:
- id: String, a URL-safe slug used in the route.
- name: String.
- description: String, a short text of 1-2 sentences.
- priceCents: int, integer minor units, never double.
- currency: String, the ISO 4217 code, always 'USD' in M1.
- placeholderColor: PlaceholderColor, an enum token resolved to a Color via the PlaceholderPalette ThemeExtension. The catalog data itself contains no Color literals, keeping all colors in the theme.

The 8 bundled products (illustrative prices chosen by the team):

| id | name | priceCents | placeholderColor |
|---|---|---|---|
| lipstick | Velvet Matte Lipstick | 1999 | rose |
| foundation | Silk Finish Foundation | 3450 | sand |
| mascara | Volume Lash Mascara | 1575 | charcoal |
| face-serum | Glow Vitamin C Face Serum | 4200 | amber |
| moisturizer | Daily Hydra Moisturizer | 2899 | mint |
| perfume | Bloom Eau de Parfum | 6500 | lavender |
| nail-polish | Gloss Nail Polish | 999 | coral |
| brush-set | Pro Makeup Brush Set | 3999 | taupe |

Placeholder palette tokens are chosen so text on top meets at least 4.5:1 contrast. Tile text is rendered below the color block on the surface color, so it does not rely on block contrast.

Display formatting uses formatMoney(int minor, String currency):
- The symbol comes from a small map ({'USD': '$'}).
- The value is `symbol + (minor ~/ 100).toString() + '.' + (minor % 100).toString().padLeft(2, '0')`.
- Examples: 1999 -> $19.99, 999 -> $9.99, 6500 -> $65.00.
- Negative amounts are not possible in M1.

The cart is CartState(productIds: List<String>) with count = length. It counts total items added and is memory only.

Future model (contract and Prisma, not deployed in M1):
- The OpenAPI Product schema mirrors the Dart Product: id, name, description, price {amountMinor: integer, currency: string}, placeholderColor.
- The Prisma Product model stores priceMinor Int and currency CHAR(3).
- Variants, stock (per variant, with reservation at checkout), carts per signed-in user, orders with copied name/unit price, payments via Stripe PaymentIntents, and users/addresses follow the project domain rules. They are intentionally NOT modeled yet because no M1 story needs them, and they will be added contract-first in the milestone that introduces them.
- The pagination envelope (items, total, page, pageSize) is defined now so future list endpoints are consistent.

## Security
- No network access in M1: the app makes zero HTTP calls and has no dio/api_client dependency. The release AndroidManifest (android/app/src/main) does not declare the INTERNET permission. Only the Flutter-generated debug/profile manifests include it for hot reload and tooling.
- No cleartext exception is added in M1 because there is no staging backend to reach. When the backend milestone starts, add a debug-only network_security_config.xml under android/app/src/debug permitting cleartext only for 10.0.2.2. Release stays https-only.
- No personal data: no accounts, sign-in, analytics, crash reporting SDKs, device identifiers or local storage. flutter_secure_storage is not added because there are no tokens.
- No payments or card data of any kind. There is no checkout UI and no Stripe SDK in M1.
- No secrets in the repository: the app needs no API keys or environment variables.
- Dependency minimization: only flutter_riverpod and go_router (plus flutter_lints/flutter_test/integration_test as dev deps) from pub.dev verified publishers, with versions pinned in pubspec.lock and committed.
- Input handling: the only external input is the route parameter productId. It is looked up in the bundled catalog, and an unknown id renders a not-found state instead of throwing.
- Future contract: the OpenAPI document already declares bearerAuth (JWT) as the global default, with /health explicitly public (security: []). This means future business endpoints are secure by default.
- Accessibility as a quality gate: every tile, button and badge has a Semantics label, and interactive elements have a minimum 48x48dp target. Widget tests assert this with meetsGuideline(androidTapTargetGuideline) and labeledTapTargetGuideline.

## Architecture decisions
### ADR-001: Bundle a local hard-coded catalog; no backend or API in M1
**Context:** The PRD requires the app to run with `flutter run` on an Android emulator within 10 minutes of scaffold. It must have no backend, network or setup, and it must work fully offline. The scope rules forbid backend work that slows delivery.

**Decision:** Ship the 8 products as const Dart data in LocalCatalogRepository, which implements a CatalogRepository interface (listProducts, findById). No NestJS service, database, docker-compose or /health endpoint is built in M1. The OpenAPI and Prisma artifacts are kept as design-only documents.

**Consequences:** Pros:
- Zero setup, instant rendering, deterministic tests.

Cons:
- Catalog changes require an app rebuild.
- There is no real data.

The repository interface lets a later milestone add an ApiCatalogRepository (backed by the generated dart-dio client) by overriding catalogRepositoryProvider, without touching screens.

### ADR-002: Keep the project conventions (feature-first, Riverpod, go_router, theme tokens) even for the demo, but skip code generation
**Context:** The demo must be tiny, but developers need an extensible base. freezed/json_serializable and the generated API client require build_runner and extra setup, which threatens the 10-minute target and adds no value without JSON/HTTP.

**Decision:** Use the lib/features/<feature>/{data,domain,presentation} and lib/core/{theme,router,money,widgets} layout, flutter_riverpod (Provider/Notifier) and go_router with one route per screen. The Product and CartState classes are written by hand as immutable classes. freezed, json_serializable, dio and packages/api_client are not added until the first milestone with an API.

**Consequences:** The structure matches later milestones, so there is no rewrite. The build needs no codegen step, and `flutter run` works immediately after `flutter pub get`, which the flutter tool runs automatically. The small cost is hand-written equality/copyWith, which can be replaced with freezed later.

### ADR-003: Money as integer minor units with ISO 4217 code, formatted with integer arithmetic
**Context:** Project convention forbids floats for prices. The common intl NumberFormat.currency API takes num and would invite dividing cents by 100.0.

**Decision:** Store priceCents as int with currency 'USD'. Format only for display in lib/core/money/format_money.dart using ~/ and %, as in 1999 -> '$19.99'. The future API models money as {amountMinor: integer, currency: string}, and Prisma stores priceMinor Int plus currency CHAR(3).

**Consequences:** No rounding errors, and the same shape flows unchanged to the backend and orders later. Formatting is limited to currencies with 2 decimal places and a small symbol map. That is sufficient for USD-only M1, and it can be replaced with an intl-based formatter fed from integer parts when more currencies arrive.

### ADR-004: In-memory cart as a Riverpod Notifier counting total items added
**Context:** US-003 (priority could) needs an Add to cart button and an app bar badge. Quantities, removal, a cart screen and persistence are out of scope, and the cart must be empty after restart.

**Decision:** CartNotifier holds an immutable list of added product ids. The badge shows its length and is hidden at 0. State lives in the root ProviderScope only, with no shared_preferences or storage.

**Consequences:** Trivially testable, and it restarts empty by design. Keeping product ids (not just an int) preserves the information needed for a future cart screen. The server-side cart for signed-in users will replace it later, in line with the domain rule that carts belong to signed-in users. The feature can be cut without affecting the catalog.

### ADR-005: Minimal forward-looking contract: health check only, shared schemas predeclared
**Context:** Contract-first is a project rule, but the M1 stories need zero API operations. Scope rules cap operations at 4 and require the health check in the contract.

**Decision:** openapi.yaml (OpenAPI 3.1) contains only GET /api/v1/health (operationId getHealth, public). It also includes components for Error {statusCode, error, message}, Money, Product, ProductPage (items/total/page/pageSize), PaginationPage/PageSize parameters and the bearerAuth JWT scheme, applied globally. The Prisma schema contains only the Product model. Neither is implemented or deployed in M1.

**Consequences:** Developers have no unused endpoints to build. The first backend milestone begins from an agreed error format, auth default, pagination envelope and Product shape that already match the Flutter model. Business endpoints (for example listProducts, getProduct) will be added contract-first when a story needs them.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.