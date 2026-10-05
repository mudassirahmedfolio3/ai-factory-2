# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1F4E79 | #9CC4EC |
| onPrimary | #FFFFFF | #0B2A45 |
| background | #FFFFFF | #121212 |
| surface | #F5F6F8 | #1E1E1E |
| onSurface | #1B1F23 | #E6E8EB |
| onSurfaceVariant | #4A5460 | #B5BCC4 |
| outline | #C9CED4 | #3A3F45 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| stockInContainer | #E3F4E8 | #1F3A29 |
| onStockInContainer | #145A2E | #B8EBC8 |
| stockOutContainer | #FDECEA | #4A1F1C |
| onStockOutContainer | #8C1D18 | #F9DEDC |
| placeholderBackground | #E4E7EB | #2A2E33 |
| placeholderIcon | #5F6B77 | #A0A8B1 |
| inverseSurface | #2F3337 | #E6E8EB |
| onInverseSurface | #F4F5F6 | #1B1F23 |
| disabledContainer | #E0E3E7 | #2E3338 |
| onDisabled | #6B737B | #8A929A |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineMedium | 24.0 | 700 | 1.3 |
| titleLarge | 20.0 | 600 | 1.3 |
| titleMedium | 16.0 | 600 | 1.4 |
| priceLarge | 22.0 | 700 | 1.3 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.45 |
| labelLarge | 14.0 | 600 | 1.4 |
| labelSmall | 12.0 | 600 | 1.35 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 999 dp.

## Shared widgets
- **ProductListTile**: List row for ProductListScreen with fixed itemExtent (96dp + 8dp gap) for smooth scrolling at 300+ items. Layout: 72x72dp ProductImage thumbnail (radius 8, decoded lazily with cacheWidth), then name (titleMedium, max 2 lines), PriceText, and StockBadge. Whole row is tappable, minimum 48dp height, with Semantics label such as 'Product name, £12.99, in stock. Double tap to view details'. Out-of-stock rows remain visible with StockBadge and use onSurfaceVariant text for the name; no hard-coded colours.
- **ProductImage**: Image widget that loads lazily and shows a placeholder (placeholderBackground with an image icon in placeholderIcon) when imageUrl is null or fails to load (errorBuilder), so the app never crashes. Supports a cacheWidth parameter. Always has a Semantics label (product name, or 'No image available' for the placeholder).
- **PriceText**: Displays an integer-pence amount via formatMoney in UK tax-inclusive format (e.g. 1299 -> £12.99), GBP only, never floats. Variants: list (titleMedium) and detail (priceLarge). Uses onSurface colour. Scales with dynamic text size.
- **StockBadge**: Pill badge (radius 999, min height 24dp, labelSmall) showing 'In stock' (stockInContainer/onStockInContainer) or 'Out of stock' (stockOutContainer/onStockOutContainer). Conveys state with text as well as colour; Semantics label 'In stock' or 'Out of stock'.
- **CartBadgeButton**: App bar IconButton (48x48dp minimum) with a shopping cart icon and a count badge watching cartProvider.itemCount; badge hidden when count is 0. Shown only when the cart feature is enabled. Navigates to /cart. Semantics label 'Cart, N items' (or 'Cart, empty').
- **LoadingView**: Centred CircularProgressIndicator (primary colour) with Semantics label 'Loading'. Used for loading states of list and detail screens.
- **EmptyView**: Centred icon, title (titleLarge) and optional message (bodyMedium, onSurfaceVariant) with an optional action button (48dp high). Used for 'No products available' and 'Your cart is empty' (action 'Browse products').
- **ErrorView**: Centred error icon (error colour), message (bodyLarge) and a 'Retry' FilledButton (48dp high) that calls ref.invalidate on the relevant provider. Variant for ProductNotFound shows 'Product not found' with a 'Back' action instead of retry. Semantics announce the error message.
- **AddToCartButton**: Full-width FilledButton, 48dp minimum height, radius 12, label 'Add to cart'. Disabled (disabledContainer/onDisabled) with label 'Out of stock' when inStock is false. On tap calls cartProvider.notifier.add(...) and shows a SnackBar confirmation (inverseSurface, e.g. 'Added to cart'). Semantics label 'Add <product name> to cart'; when disabled, 'Add to cart unavailable, out of stock'.
- **QuantityStepper**: Cart line stepper with decrement and increment IconButtons (each 48x48dp) and a quantity label between them (minimum 1, maximum stockQuantity; increment disabled at max). Semantics labels 'Decrease quantity of <name>', 'Increase quantity of <name>', and 'Quantity N'.
- **CartLineTile**: Cart row showing ProductImage thumbnail (56dp), name, unit price (PriceText), QuantityStepper and a remove IconButton (48x48dp, Semantics 'Remove <name> from cart'). Quantity and total update immediately on change.
- **AppTheme**: lib/core/theme: single central theme file building light and dark ThemeData from the colour, typography, spacing and corner-radius tokens in this design system (Material 3, ColorScheme from tokens, ThemeMode.system). Widgets never hard-code colours or sizes; tokens are easy to swap.

## Screens
### SCR-01 Product List (`/`)
Launch screen and default route. Shows a scrollable list of products from the local mock catalogue (thumbnail, name, tax-inclusive price in £ format, stock status) with no sign-in prompt. Uses productListProvider (AsyncNotifier<ProductListState>) calling catalogRepositoryProvider.listProducts(page, pageSize: 20) with infinite scroll appending pages near the end. ListView.builder with itemExtent and PageStorageKey to preserve scroll position; thumbnails decoded lazily with cacheWidth. Out-of-stock products remain visible and clearly marked.
- Components: AppBar (title 'Simple Shop'), CartBadgeButton (only when cart feature enabled), ListView.builder with itemExtent and PageStorageKey, ProductListTile, ProductImage, PriceText, StockBadge, LoadingView, EmptyView, ErrorView
- States: loading: LoadingView spinner while first page loads; small bottom spinner row while next page loads, empty: EmptyView with message 'No products available', error: ErrorView with Retry that calls ref.invalidate(productListProvider), data: list of ProductListTile rows; out-of-stock rows show the 'Out of stock' StockBadge; missing images show placeholder
- Stories: US-001

### SCR-02 Product Detail (`/products/:productId`)
Nested under '/'. Shows full product details so the shopper can decide whether to buy: image, name, description, tax-inclusive GBP price and stock availability (in stock or out of stock). Uses productDetailProvider (FutureProvider.autoDispose.family<ProductDetail, String>) calling catalogRepositoryProvider.getProduct(productId). Provides Add to cart (disabled when out of stock) with SnackBar confirmation. Back (app bar back button or system back gesture) returns to the still-mounted list at the same scroll position.
- Components: AppBar with back button, CartBadgeButton (only when cart feature enabled), ProductImage (large, placeholder fallback), Product name (headlineMedium), PriceText (detail variant), StockBadge, Description text (bodyLarge), AddToCartButton (48dp, semantic label), SnackBar confirmation, LoadingView, ErrorView
- States: loading: LoadingView spinner, error: ErrorView with Retry (ref.invalidate(productDetailProvider)); ProductNotFound shows 'Product not found' with a back action, data: full details shown; in stock enables AddToCartButton, out-of-stock: 'Out of stock' StockBadge shown and AddToCartButton disabled, no-image: placeholder image shown instead of product image without crashing, empty: not applicable (a missing product is handled as the ProductNotFound error state)
- Stories: US-002, US-003

### SCR-03 Cart (`/cart`)
Could-have (delivered only if time allows). In-memory cart listing each added item with name, quantity stepper and unit price, and the cart total (sum computed in integer pence, formatted £x.xx via formatMoney). Uses cartProvider (NotifierProvider<CartNotifier, CartState>) with add, increment, decrement, setQuantity (min 1, max stockQuantity) and remove. Lines and total update immediately. No persistence (relaunch yields an empty cart). No checkout button in this release.
- Components: AppBar with back button (title 'Cart'), ListView of CartLineTile, QuantityStepper, PriceText, Total row (titleLarge label 'Total' and PriceText), EmptyView with 'Browse products' action
- States: loading: not applicable (in-memory state is synchronous), empty: EmptyView 'Your cart is empty' with 'Browse products' action navigating to /, error: not applicable (no network or persistence); quantity limited to stockQuantity with increment disabled at max, data: CartLineTiles with live total; removing or changing quantity updates lines and total immediately
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap a ProductListTile row -> context.go/push('/products/:productId')
- SCR-02 → SCR-01: App bar back button or system back gesture -> list remains mounted and keeps scroll position (PageStorageKey)
- SCR-02 → SCR-01: Back action on the 'Product not found' ErrorView
- SCR-01 → SCR-03: Tap CartBadgeButton in app bar -> '/cart' (only when cart feature enabled)
- SCR-02 → SCR-03: Tap CartBadgeButton in app bar -> '/cart' (only when cart feature enabled)
- SCR-03 → SCR-01: Tap 'Browse products' in the empty cart state -> '/'
- SCR-03 → SCR-02: App bar back button or system back gesture returns to the previous screen (detail or list) in the navigation stack

## Accessibility
- Minimum touch target 48x48dp for all interactive elements (list rows, CartBadgeButton, AddToCartButton, QuantityStepper buttons, remove buttons, Retry and other action buttons).
- Text contrast at least WCAG 2.1 AA (4.5:1 for body text, 3:1 for large text and UI components) for all light and dark token pairs; stock state is never conveyed by colour alone (badge always has 'In stock' / 'Out of stock' text).
- Dynamic text sizing supported: all text uses theme text styles that scale with system font size; layouts avoid fixed heights for text (ProductListTile uses itemExtent with overflow ellipsis and max lines, and must be verified at large text scale).
- TalkBack semantic labels on all buttons, images and interactive elements, including product images (product name or 'No image available' for placeholder), CartBadgeButton ('Cart, N items'), AddToCartButton, QuantityStepper and remove buttons.
- ProductListTile merges its semantics into a single readable label: name, price, stock status.
- Loading, error and empty states are announced to screen readers (Semantics labels on LoadingView, ErrorView and EmptyView); SnackBar confirmation after adding to cart is announced as a live region.
- Prices read in full UK format (e.g. '£12.99') and formatted only via formatMoney from integer pence.
- Light and dark themes both supported via ThemeMode.system using tokens from lib/core/theme; no hard-coded colours or sizes in widgets.
- Keyboard/focus order follows visual order (app bar, content, actions); back navigation is available on all non-root screens via the app bar back button and system back gesture.
- Widget tests per screen (list and detail) include checks for semantic labels and out-of-stock disabled state.