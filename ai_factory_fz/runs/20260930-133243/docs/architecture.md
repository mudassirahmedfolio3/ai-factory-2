# Architecture

ShopEasy M1 Speed Demo is a single Flutter 3.x Android-first app with three screens (product list, product detail, in-memory cart), backed entirely by a local mock catalogue bundled in the app. M1 has no backend, no network calls, no authentication, no payments and no persistence, so the app runs on an Android emulator with no setup. Coding starts in WI-001.

Architecture in one paragraph: the app follows the feature-first convention (lib/features/<feature>/{data,domain,presentation}, shared code in lib/core). The catalog feature defines a domain-level CatalogRepository interface. M1 provides only MockCatalogRepository, which serves an immutable const list of at least 8 products (each with at least one variant and an integer stock) from lib/features/catalog/data/mock_catalogue.dart. Riverpod providers expose the catalogue to the list and detail screens as AsyncValue so loading, empty and error states are real code paths. The cart feature is a Riverpod Notifier holding an immutable in-memory CartState keyed by variantId; it is lost when the app process ends, as US-003 requires. go_router defines exactly three routes: / (ProductListScreen), /products/:productId (ProductDetailScreen, pushed on top of the list so the list and its scroll position stay alive), and /cart (CartScreen). All money is integer minor units (pence) with ISO 4217 code GBP, formatted by a single integer-only formatter in lib/core/money (e.g. 1999 -> £19.99, VAT-inclusive, en-GB). The theme is one token set in lib/core/theme chosen by the build agent with no approval step.

Contract and future path: the OpenAPI 3.1 document contains only the infrastructure operation GET /api/v1/health (does not count toward the 4-operation limit; 0 business operations are needed in M1) plus shared schemas (Money, Product, ProductSummary, ProductVariant, StockStatus, ProductPage, Error, pagination parameters, bearerAuth scheme). The local domain models mirror those schemas field-for-field so a later catalog API can replace MockCatalogRepository with an implementation over the generated dart-dio client without touching presentation code. The Prisma schema defines only Product and ProductVariant, mirroring the mock; it is not deployed in M1 and exists so the future backend starts from an agreed model.

Folder layout (M1):
lib/main.dart (ProviderScope + MaterialApp.router)
lib/core/theme/{tokens.dart, app_theme.dart}
lib/core/router/app_router.dart
lib/core/money/money.dart (Money value type + formatGbp)
lib/core/widgets/{async_value_view.dart, product_image.dart, empty_state.dart, error_state.dart, cart_badge_button.dart}
lib/features/catalog/domain/{product.dart, product_variant.dart, stock_status.dart, catalog_repository.dart}
lib/features/catalog/data/{mock_catalogue.dart, mock_catalog_repository.dart}
lib/features/catalog/presentation/{product_list_screen.dart, product_detail_screen.dart, providers.dart, widgets/}
lib/features/cart/domain/{cart_line.dart, cart_state.dart}
lib/features/cart/presentation/{cart_notifier.dart, cart_screen.dart, widgets/}
assets/images/products/ (optional small bundled images; placeholder widget otherwise)
test/ (unit + widget tests), integration_test/browse_to_cart_test.dart

Work item mapping: WI-001 project skeleton, core/money, core/theme skeleton, router, domain models, mock catalogue; WI-002 list screen + providers; WI-003 detail screen with variant selection and stock status; WI-004 cart notifier, badge and cart screen; WI-005 final theme tokens, accessibility pass, widget and integration tests.

## Components
- **ShopEasy Flutter app (Android first)** (Flutter 3.x, Dart 3, Android emulator (API 34), flutter_riverpod, go_router): Single codebase app that launches directly into the product list, hosts the three M1 screens and runs fully offline on an Android emulator. Bootstraps ProviderScope and MaterialApp.router with the app theme.
- **core/router** (go_router): Declares exactly three routes, one per screen spec: '/' ProductListScreen, '/products/:productId' ProductDetailScreen (pushed with context.push so the list stays mounted and keeps scroll position), '/cart' CartScreen. Unknown productId renders the detail screen's not-found error state.
- **core/theme** (Flutter ThemeData, Material 3 ColorScheme.fromSeed with contrast-checked on-colours): Single source of design tokens (colour scheme, typography with body text >= 14sp, spacing scale, radii, minimum touch target 48dp) and the ThemeData built from them. Widgets read only from Theme/tokens; no hard-coded colours or sizes. Tokens are chosen by the build agent; no approval step.
- **core/money** (Pure Dart (no intl currency formatting, to avoid double conversion)): Immutable Money value type (int amountMinor, String currency) and integer-only formatting: pounds = amountMinor ~/ 100, pence = amountMinor % 100 padded to 2 digits, thousands grouped with commas, prefixed with £ (e.g. 1999 -> £19.99, 2499 -> £24.99, 123456 -> £1,234.56). Addition and multiplication by int quantity only; asserts currency == GBP. Never converts to double.
- **core/widgets** (Flutter widgets, Semantics): Shared widgets: AsyncValueView (loading/empty/error rendering for AsyncValue), ProductImage (Image.asset with cacheWidth sized for mobile and a semantic label, falling back to a themed placeholder icon with the same label), EmptyState, ErrorState with retry, CartBadgeButton (app-bar cart icon with item count, 48dp target, semantic label 'Cart, N items').
- **catalog feature** (Dart immutable classes, flutter_riverpod (FutureProvider / FutureProvider.family), ListView.builder): Domain models Product, ProductVariant, StockStatus; CatalogRepository interface (listProducts(), getProduct(id)); MockCatalogRepository backed by the bundled const catalogue; Riverpod providers for the product list and a single product; ProductListScreen and ProductDetailScreen.
- **Mock catalogue data source** (Dart const data in lib/features/catalog/data/mock_catalogue.dart): Const Dart list of at least 8 GBP products with stable string ids, name, description, priceMinor (int pence, VAT-inclusive), optional asset image path and 1..n variants each with sku, label (e.g. size) and integer stock. Must include at least one product with multiple variants, one variant with stock 0, one low-stock variant (1-5), and a product priced 1999 and one priced 500 for acceptance tests.
- **cart feature** (flutter_riverpod Notifier, pure Dart): In-memory cart: CartNotifier (Riverpod Notifier<CartState>) with add(product, variant), increment(variantId), decrement(variantId), remove(variantId); derived itemCount and total (integer pence). Enforces quantity >= 1 and <= variant mock stock, rejects out-of-stock variants. CartScreen shows lines, quantity controls, remove and total; no checkout or payment control. No persistence.
- **Test suites** (flutter_test, integration_test, ProviderScope overrides): Unit tests for money formatting and CartNotifier rules; widget tests per screen (list, detail, cart) covering loading, empty and error states with overridden repository providers; one integration_test journey launch -> list -> detail -> select variant -> add to cart -> cart total.
- **Health API (deferred, contract only)** (NestJS, @nestjs/terminus-style check via PrismaService, PostgreSQL 16 (future)): GET /api/v1/health returning 200 when the database is reachable. Defined in the contract so any future backend starts with it; not built or deployed in M1.
- **Generated API client (deferred)** (openapi-generator dart-dio (future)): packages/api_client generated from openapi_yaml with dart-dio when the first business endpoint is added. Not generated or depended on in M1 because the app makes no HTTP calls.

## Backend modules
### health (deferred - not built in M1)
Infrastructure liveness check. Returns 200 { status: ok, database: up } when a trivial query (SELECT 1) through PrismaService succeeds, otherwise 503 with the shared Error body. Public, no auth. Built only when a backend is introduced in a later milestone; M1 has no backend work.
Entities: 

- `GET /api/v1/health`

## Mobile app features
- catalog (browse and product detail) - US-001, US-002: screens ProductListScreen - route '/' (home): app bar with title and CartBadgeButton; ListView.builder of ProductCard (ProductImage, name, formatted price) with PageStorageKey('product-list') so scroll position is kept; tap card -> context.push('/products/<id>'); states: loading (progress indicator), empty ('No products available'), error (message + Retry which invalidates the provider), ProductDetailScreen - route '/products/:productId': image, name, description, price (VAT-inclusive GBP), variant selector (ChoiceChips, each >= 48dp, out-of-stock chips disabled with label '<size>, out of stock'), stock status text for the selected variant (In stock / Low stock - only N left / Out of stock), Add to cart button enabled only when an in-stock variant is selected; back via app-bar back button or system back returns to list at the same scroll position; states: loading, not-found/error, and product with no selectable variant (all out of stock) shows 'Out of stock' and a disabled button (state: Riverpod. catalogRepositoryProvider = Provider<CatalogRepository>((ref) => MockCatalogRepository()) (overridden in tests to simulate loading/empty/error). productListProvider = FutureProvider<List<Product>> calling repository.listProducts(). productDetailProvider = FutureProvider.family<Product, String>(productId) calling repository.getProduct(id), throwing ProductNotFound for unknown ids. Selected variant is local screen state: selectedVariantProvider = NotifierProvider.autoDispose.family<SelectedVariantNotifier, String?, String>(productId), initialised to the only variant if the product has exactly one in-stock variant, otherwise null. StockStatus is derived, never stored: stock == 0 -> outOfStock, 1..5 (lowStockThreshold = 5 in domain) -> lowStock, > 5 -> inStock. MockCatalogRepository returns Future.value synchronously-completed data so the list renders well within 3 seconds.)
- cart (in-memory) - US-003: screens CartScreen - route '/cart': list of CartLineTile (product name, variant label, unit price, quantity with decrement/increment IconButtons >= 48dp and semantic labels, Remove button), total row 'Total £X.XX' computed from integer pence; decrement disabled at quantity 1 (use Remove), increment disabled at variant stock; empty state message 'Your cart is empty' with a 'Browse products' button back to '/'; no checkout or payment control in any state (state: Riverpod Notifier: cartProvider = NotifierProvider<CartNotifier, CartState> (not autoDispose, lives for the app process only; nothing is written to disk, so relaunch starts empty). CartState is an immutable ordered list of CartLine { variantId, productId, productName, variantLabel, unitPriceMinor (int), currency 'GBP', quantity (int), maxQuantity (int, copied from variant stock) }. Operations: add(product, variant) -> if variant.stock == 0 no-op/throws; if line exists increment (capped at maxQuantity) else append with quantity 1; increment(variantId) capped at maxQuantity; decrement(variantId) floored at 1; remove(variantId). Derived providers: cartItemCountProvider (sum of quantities, used by CartBadgeButton on every screen) and cartTotalProvider (Money, sum of unitPriceMinor * quantity in int). Product name and unit price are copied into the line at add time, matching the order-line convention.)

## Data model
M1 runtime data lives only in the app: the bundled const mock catalogue and the in-memory cart. No database is deployed in M1; the Prisma schema below is the agreed future shape of the catalog tables and is intentionally limited to Product and ProductVariant because those are the only entities the three stories touch. User, Address, Category, Cart, CartItem, Order, OrderItem and Payment are deferred with their features (auth, persistent cart, checkout, Stripe) and must be added in the milestone that introduces them.

Money: every price is an int amountMinor in minor units (pence) plus a 3-letter ISO 4217 currency code; M1 accepts only GBP. Prices are stored and shown VAT-inclusive (UK standard 20% already included); no VAT is computed in the app. Formatting and totals use integer arithmetic only (~/ and %), never double. In the API contract this is the Money schema { amountMinor: integer >= 0, currency: 'GBP' }; in Prisma it is priceMinor Int + currency Char(3).

Price lives on Product; variants inherit the product price (sizes do not change price in M1). If per-variant pricing is needed later, add a nullable priceMinor override on ProductVariant.

Stock is tracked per ProductVariant as a non-negative int. StockStatus (in_stock, low_stock, out_of_stock) is derived, not stored: 0 -> out_of_stock, 1-5 -> low_stock, >5 -> in_stock. In M1 stock is never decremented by the cart (no reservation; reservation belongs to future checkout); the cart only caps quantity at the variant's mock stock.

Identifiers: mock products use stable string ids (e.g. 'p-001') and variants use their SKU-like ids (e.g. 'p-001-m'); the contract types ids as string so the future UUIDs from Prisma are compatible. Mock image paths are optional asset paths (assets/images/products/<id>.webp, small, <= 600px wide); null or failed loads render the placeholder.

Cart lines copy productName, variantLabel and unitPriceMinor at add time, matching the project rule that order lines snapshot name and price.

Database-level constraints to add as raw SQL in the first migration when the backend exists (Prisma cannot express them): CHECK (price_minor >= 0) on products, CHECK (currency ~ '^[A-Z]{3}$') on products, CHECK (stock >= 0) on product_variants.

## Security
- M1 attack surface is minimal by design: no backend, no network calls, no authentication, no accounts, no personal data, no analytics or tracking SDKs, no payment or card data. Do not add the INTERNET-dependent packages or any third-party SDKs in M1.
- No secrets exist in M1; nothing is stored on device except the bundled read-only catalogue. The cart is held in memory only and is not written to shared preferences, files or secure storage.
- Android release build stays https-only (no cleartext). The debug-only network-security config (android/app/src/debug/res/xml/network_security_config.xml allowing cleartext for 10.0.2.2 only) is added in the milestone that introduces the backend; it is not needed in M1 because the app makes no HTTP calls.
- Dependency hygiene: pin Flutter and package versions in pubspec.lock, keep dependencies to flutter_riverpod and go_router (plus dev test packages) for M1, and run flutter analyze with no warnings in CI.
- Input safety: the only external input is the route parameter productId, which is only used as a lookup key in the in-memory catalogue; unknown ids render a not-found error state rather than throwing.
- Future backend (deferred, contract already reflects it): all business endpoints will require JWT bearer auth (bearerAuth scheme, 15-minute access tokens plus refresh tokens) except public catalog reads and GET /api/v1/health; access tokens stored with flutter_secure_storage; passwords hashed with argon2id; errors use the shared { statusCode, error, message } body without stack traces; config validated at startup via @nestjs/config; Stripe card data never touches the server.
- Accessibility is treated as a quality gate: every image and icon has a semantic label, all tap targets are at least 48x48dp, body text is at least 14sp and theme colour pairs meet WCAG AA contrast (4.5:1 for body text).

## Architecture decisions
### ADR-001: Bundled local mock catalogue; no backend in M1
**Context:** The PRD and run scope require the smallest runnable Flutter MVP that works on an Android emulator immediately, with 0 API operations needed and backend work explicitly out of scope if it slows delivery. The product team must launch the demo with no setup.

**Decision:** Ship the catalogue as const Dart data inside the app (lib/features/catalog/data/mock_catalogue.dart) behind a domain CatalogRepository interface, implemented in M1 only by MockCatalogRepository. No NestJS service, database, Docker or network access is built for M1. The OpenAPI document contains only GET /api/v1/health plus shared schemas that the domain models mirror, and the Prisma schema captures the future Product/ProductVariant tables.

**Consequences:** The app runs offline instantly and meets the 3-second launch target easily. There is zero backend cost or risk in M1. Catalogue changes need an app rebuild, which is acceptable for a demo. When a real catalog API is added, an ApiCatalogRepository over the generated dart-dio client replaces the mock via one provider override, with no change to screens, as long as the new endpoints return the ProductSummary/Product/ProductPage schemas already defined in the contract.

### ADR-002: Integer minor-unit money with an integer-only GBP formatter
**Context:** Project rules and the PRD require prices as integer minor units with ISO 4217 codes and never floats, with acceptance tests such as 1999 -> £19.99 and 1999 + 500 -> £24.99. Common Flutter currency formatting (intl NumberFormat.currency) takes a num and would require dividing by 100 into a double.

**Decision:** Introduce a Money value type (int amountMinor, String currency) in lib/core/money with integer-only operations (add, multiply by int quantity) and a formatGbp function that builds the string from amountMinor ~/ 100 and amountMinor % 100 with comma thousands grouping and a £ prefix. All screens and the cart total use it; prices are VAT-inclusive as stored. Only GBP is accepted in M1 (assert).

**Consequences:** No floating-point rounding errors are possible and formatting is trivially unit-testable. Negative amounts and non-GBP currencies are unsupported until needed (multi-currency is out of scope). A small amount of custom code replaces intl, which must be revisited only if multiple locales or currencies are added.

### ADR-003: Riverpod Notifier for an in-memory, non-persistent cart
**Context:** US-003 (could) needs add, quantity change, remove, a live item-count badge and a total, and explicitly requires the cart to be empty after relaunch. Guest carts and persistent carts are out of scope, and the cart is the first thing to cut if delivery is at risk.

**Decision:** Implement the cart as a single app-lifetime NotifierProvider<CartNotifier, CartState> with immutable state keyed by variantId, derived providers for item count and total, and no storage layer. Business rules (quantity between 1 and the variant's mock stock, no out-of-stock adds) live in the notifier, not in widgets. Lines snapshot product name, variant label and unit price at add time.

**Consequences:** Simple, testable with plain unit tests and cheap to cut: removing the cart feature means deleting lib/features/cart, the /cart route and the badge. Cart contents are lost on process death by design. When sign-in and server carts arrive, the notifier will be backed by the cart API and the persistence decision revisited.

### ADR-004: Three go_router routes with the detail screen pushed over the list
**Context:** US-002 requires that back (button or system gesture) returns to the product list at the same scroll position, and the conventions require one route per screen spec with go_router. Scope allows at most 3 screens.

**Decision:** Define exactly '/', '/products/:productId' and '/cart'. Navigate to detail and cart with context.push so the list route stays mounted underneath; the list's ListView uses a PageStorageKey as a second guarantee of scroll restoration. No ShellRoute or bottom navigation.

**Consequences:** Scroll position is preserved without custom state, and deep links to a product id work for tests. The list remains in memory while detail is open, which is negligible with a small mock catalogue. Adding tabs later would require introducing a StatefulShellRoute.

### ADR-005: Derived stock status with a fixed low-stock threshold
**Context:** US-002 requires each variant to show in stock, low stock or out of stock, with stock 0 not selectable. The PRD does not define low stock.

**Decision:** Store only the integer stock per variant. Derive StockStatus in the domain layer: 0 -> out of stock, 1 to 5 -> low stock (lowStockThreshold = 5 constant), more than 5 -> in stock. The contract exposes the same derived stockStatus enum alongside stock for future API responses.

**Consequences:** One rule, one place, unit-testable, and consistent between mock and future API. Changing the threshold is a one-line change. Real stock reservation remains a future checkout concern.

The API contract is in `openapi.yaml`; the data model is in `schema.prisma`.