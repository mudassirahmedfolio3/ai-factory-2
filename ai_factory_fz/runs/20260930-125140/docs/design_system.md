# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #0B57D0 | #A8C7FA |
| onPrimary | #FFFFFF | #062E6F |
| background | #FAFAFA | #121212 |
| surface | #FFFFFF | #1E1E1E |
| surfaceVariant | #E8EAF0 | #2C2F36 |
| onSurface | #1B1B1F | #E3E3E8 |
| onSurfaceVariant | #44474F | #C4C6D0 |
| outline | #74777F | #8E9099 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| success | #1B6E3A | #7FD79A |
| outOfStockContainer | #F9DEDC | #8C1D18 |
| onOutOfStockContainer | #410E0B | #F9DEDC |
| badge | #B3261E | #F2B8B5 |
| onBadge | #FFFFFF | #601410 |
| selectedContainer | #D3E3FD | #0842A0 |
| onSelectedContainer | #041E49 | #D3E3FD |
| disabledContainer | #E0E2E8 | #3A3C42 |
| onDisabled | #5F6168 | #A9ABB3 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineMedium | 28.0 | 700 | 36.0 |
| titleLarge | 22.0 | 600 | 28.0 |
| titleMedium | 16.0 | 600 | 24.0 |
| price | 18.0 | 700 | 24.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| labelLarge | 14.0 | 600 | 20.0 |
| labelSmall | 12.0 | 500 | 16.0 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 999 dp.

## Shared widgets
- **AppStrings**: Single English (US) string source in lib/core (e.g. app_strings.dart) holding all user-visible text, including 'No products available', 'Out of stock', 'In stock', 'Add to cart', 'Browse products', 'Retry', empty-cart message and all semantic labels. No hard-coded text or currency symbols in widgets.
- **MoneyFormatter**: Formats integer minor units (cents) with an ISO 4217 currency code (USD) into a display string (1999 -> $19.99) using the currency code, never a hard-coded symbol and never floating-point money. Used by PriceText, ProductCard, CartLineTile and subtotal.
- **PriceText**: Text widget showing a Money value via MoneyFormatter using the price type style and onSurface color. Supports a 'from' prefix from AppStrings for priceFrom on list cards and before a variant selection on detail.
- **ProductImage**: Bundled asset image (or generated placeholder on surfaceVariant with an icon) with rounded corners and a required Semantics label (product name). Falls back to placeholder on load error; no network images.
- **OutOfStockBadge**: Pill badge (radius 999) using outOfStockContainer/onOutOfStockContainer colors with the text 'Out of stock' from AppStrings; meaning conveyed by text, not color alone. Shown on list cards when no variant has stock and on detail for an out-of-stock variant.
- **ProductCard**: Tappable card (min height 48dp, whole card is the touch target) with ProductImage, product name (titleMedium, max 2 lines, scales with system font), 'from' PriceText and OutOfStockBadge when no variant has stock. Semantics merged: name, price, availability. Tap pushes /products/:productId.
- **CartIconButton**: App bar IconButton (48x48dp) with cart icon and count badge (badge/onBadge colors) driven by cartItemCountProvider; badge hidden when 0. Semantic label 'Cart, N items'. Navigates to /cart.
- **VariantChoiceChip**: ChoiceChip for a size or color option with minimum 48dp height/width touch target. Selected state uses selectedContainer/onSelectedContainer plus a check icon and a 2dp primary outline; wrapped in Semantics(selected: true) when selected. Unavailable combinations remain selectable so out-of-stock status can be shown.
- **VariantChipGroup**: Labeled Wrap of VariantChoiceChips (section label 'Size' or 'Color', labelLarge) with 8dp spacing; reads and writes variantSelectionProvider(productId).
- **StockStatusLabel**: Text with icon showing 'In stock' (success color) or 'Out of stock' (error color) for the resolved variant, announced as a live region when the selection changes.
- **AddToCartButton**: Full-width FilledButton (min height 48dp) labelled 'Add to cart'. Disabled (disabledContainer/onDisabled) until an in-stock variant is selected and stays disabled for out-of-stock variants; semantic label states the disabled reason.
- **QuantityStepper**: Row with 48x48dp minus and plus IconButtons and a quantity text between; semantic labels 'Decrease quantity of <product>' and 'Increase quantity of <product>'. Minus at quantity 1 removes the line (quantity 0); plus disabled at the stock cap known at add time.
- **CartLineTile**: Cart row showing product name, variant label (size / color), unit price, QuantityStepper and line total (unitPrice.amountMinor * quantity in integer cents) plus a 48dp remove IconButton with semantic label 'Remove <product>'.
- **CartSubtotalBar**: Bottom summary bar with 'Subtotal' label and PriceText from cartSubtotalProvider. Contains no checkout or payment actions.
- **LoadingView**: Centered CircularProgressIndicator with a semantic label 'Loading'; shown during AsyncLoading. Optional skeleton list cards on the product list.
- **EmptyView**: Centered icon, message text and optional action button (48dp). Used for 'No products available' on list, empty cart message with 'Browse products' action on cart, and 'no variants' on detail.
- **ErrorView**: Centered error icon, error message and a 'Retry' button (48dp) that invalidates/re-reads the provider. Used for list error and detail not-found/error.
- **AppTheme**: ThemeData light and dark built from the design tokens in lib/core/theme (colors, typography, spacing, radii); widgets read tokens only and have no hard-coded colors or sizes. Follows system theme mode.

## Screens
### SCR-01 ProductListScreen (`/`)
Initial screen. Shows a smooth scrollable list of at least 12 products from the bundled local mock catalog (image or placeholder, name, 'from' price from integer cents in USD, out-of-stock badge when no variant has stock) so the shopper can quickly discover products. Scroll position is preserved when returning from detail via PageStorageKey and keeping the list mounted under the pushed detail route.
- Components: AppBar with title and CartIconButton, ListView.builder with PageStorageKey, ProductCard, ProductImage, PriceText, MoneyFormatter, OutOfStockBadge, LoadingView, EmptyView, ErrorView, AppStrings
- States: loading, empty (No products available), error (with Retry), success (scrollable product list), product out of stock (badge on card)
- Stories: US-001

### SCR-02 ProductDetailScreen (`/products/:productId`)
Shows a product's image, name, description and price (selected variant price, or priceFrom before a selection) with size and color choice chips, the selected variant's in-stock/out-of-stock status, and an Add to cart action that is enabled only for an in-stock variant. System back and app bar back pop to the list at the same scroll position.
- Components: AppBar with back button and CartIconButton, ProductImage, Product name and description text, PriceText, MoneyFormatter, VariantChipGroup (Size), VariantChipGroup (Color), VariantChoiceChip, StockStatusLabel, OutOfStockBadge, AddToCartButton, SnackBar confirmation with 'View cart' action, LoadingView, EmptyView (no variants), ErrorView, AppStrings
- States: loading, not-found/error (with Retry or back to list), no variants (message, Add to cart disabled), success, no variant selected (priceFrom shown, Add to cart disabled), variant selected in stock (variant price, In stock, Add to cart enabled), variant selected out of stock (Out of stock shown, Add to cart disabled), added to cart (cart badge updates, snackbar shown)
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Optional in-memory cart. Lists one line per variant with product name, variant label (size / color), unit price, quantity stepper and line total, plus a subtotal, all integer cents displayed in USD. No checkout or payment actions exist; the cart is lost when the app process closes.
- Components: AppBar with back button, ListView of CartLineTile, QuantityStepper, PriceText, MoneyFormatter, CartSubtotalBar, EmptyView with 'Browse products' action, AppStrings
- States: empty (empty-cart message with 'Browse products' action), success (lines and subtotal), line removed or quantity set to zero (line disappears, subtotal updates), quantity at stock cap (plus button disabled)
- Stories: US-003

## Navigation
- SCR-01 ProductListScreen → SCR-02 ProductDetailScreen: Tap a ProductCard: context.push('/products/:productId') on top of the list so the list stays mounted and keeps its scroll position
- SCR-02 ProductDetailScreen → SCR-01 ProductListScreen: App bar back button or system back: pop to the list at the same scroll position
- SCR-01 ProductListScreen → SCR-03 CartScreen: Tap CartIconButton in the app bar: context.push('/cart')
- SCR-02 ProductDetailScreen → SCR-03 CartScreen: Tap CartIconButton in the app bar or the 'View cart' action on the added-to-cart snackbar: context.push('/cart')
- SCR-03 CartScreen → SCR-01 ProductListScreen: Tap 'Browse products' in the empty cart state: context.go('/')
- SCR-03 CartScreen → Previous screen (SCR-01 or SCR-02): App bar back button or system back: pop

## Accessibility
- All interactive elements (cart icon, product cards, variant chips, quantity +/- buttons, remove button, Add to cart, Retry, Browse products, back button) have a minimum 48x48dp touch target.
- All images and icons have semantic labels: product images use the product name, the cart icon reads 'Cart, N items', decorative icons are excluded from semantics.
- Selected variant chips use Semantics(selected: true) and also show a check icon and outline so selection is not conveyed by color alone.
- Out-of-stock status is conveyed with text ('Out of stock') plus icon/badge, never by color alone; changes to stock status are announced as a live region.
- Disabled Add to cart exposes a semantic label explaining why it is disabled (select an in-stock variant).
- Text uses sp units and respects system font scaling; layouts allow wrapping (product names up to 2 lines on cards) and scrolling without clipping at 200% scale.
- Color tokens meet WCAG AA in both light and dark themes: body text at least 4.5:1, large text and UI component boundaries at least 3:1 (e.g. onSurface #1B1B1F on surface #FFFFFF, primary #0B57D0 with onPrimary #FFFFFF, dark primary #A8C7FA on #121212).
- Each product card merges its semantics into one node reading name, price and availability; cart lines read product name, variant, unit price, quantity and line total.
- Prices are read from MoneyFormatter output derived from the currency code (USD), with no hard-coded currency symbols; all text comes from the single AppStrings source for localization readiness.
- Loading, empty and error states are announced via semantic labels, and the error state offers a Retry button reachable by screen reader focus order.
- Logical focus order follows visual order (app bar, content, primary action) and dark theme follows system setting.