# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1A5FB4 | #8AB4F8 |
| onPrimary | #FFFFFF | #0B1D33 |
| background | #FFFFFF | #121212 |
| surface | #F6F7F9 | #1E1E1E |
| onSurface | #1B1B1F | #E6E6EA |
| onSurfaceVariant | #525866 | #B8BCC7 |
| outline | #767B88 | #8D919E |
| selectedContainer | #D6E4FA | #1F3A5F |
| success | #1B6E3C | #7FD6A0 |
| warning | #8A5300 | #FFC46B |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| disabled | #5F6470 | #9A9EAB |
| disabledContainer | #E3E5EA | #2E3038 |
| badge | #B3261E | #F2B8B5 |
| onBadge | #FFFFFF | #601410 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| titleLarge | 22.0 | 700 | 28.0 |
| titleMedium | 18.0 | 600 | 24.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| labelLarge | 16.0 | 600 | 20.0 |
| priceLarge | 24.0 | 700 | 32.0 |
| priceMedium | 16.0 | 700 | 24.0 |
| caption | 14.0 | 500 | 20.0 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 24 dp.

## Shared widgets
- **CartBadgeButton**: App bar IconButton (minimum 48x48dp) with a cart icon and a count badge driven by cartItemCountProvider (sum of quantities); shown on every screen except the cart screen; tap runs context.push('/cart'); semantic label 'Cart, N items'; badge hidden when the count is 0.
- **ProductCard**: Tappable card in the product list showing ProductImage, product name and formatted price; the whole card is at least 48dp tall; tap runs context.push('/products/<id>'); semantic label '<name>, <price>'.
- **ProductImage**: Lazy-loaded image (bundled asset or placeholder) sized for mobile, with a placeholder when missing and an errorBuilder fallback; always has a semantic label (product name).
- **PriceText**: Formats integer minor units (pence) with currency GBP into '£19.99' VAT-inclusive using integer arithmetic only (no floating point); uses the priceMedium/priceLarge type styles; semantic label reads the amount.
- **VariantChoiceChips**: Wrap of ChoiceChips for variant selection; each chip at least 48dp high and wide; the selected chip is highlighted with selectedContainer plus a check icon (not colour alone); out-of-stock chips are disabled with semantic label '<size>, out of stock'.
- **StockStatusText**: Text showing the selected variant's derived StockStatus: 'In stock', 'Low stock - only N left' (stock 1..5) or 'Out of stock' (stock 0); paired with an icon and colour (success, warning, error) so it is not colour only.
- **CartLineTile**: Cart row showing product name, variant label, unit price and quantity; decrement/increment IconButtons at least 48dp with semantic labels ('Decrease quantity of <name>', 'Increase quantity of <name>'); decrement disabled at quantity 1, increment disabled at variant stock; a Remove button of at least 48dp.
- **TotalRow**: Cart total row 'Total £X.XX' computed by cartTotalProvider from integer pence (sum of unitPriceMinor * quantity); announced as a live region on change.
- **LoadingView**: Centered CircularProgressIndicator with semantic label 'Loading'.
- **EmptyView**: Centered icon, message and optional action button (e.g. 'No products available', 'Your cart is empty' with 'Browse products').
- **ErrorView**: Centered error icon, message and a 'Retry' button (at least 48dp) that invalidates the relevant provider; used for load failures and product not found.

## Screens
### SCR-01 ProductListScreen (`/`)
Home screen: scrollable list of products from the local mock catalogue, each showing image, name and VAT-inclusive GBP price; tapping a card opens the product detail. Scroll position is kept via PageStorageKey('product-list') so returning from detail restores it.
- Components: AppBar with title and CartBadgeButton, ListView.builder with PageStorageKey('product-list'), ProductCard, ProductImage, PriceText, LoadingView, EmptyView, ErrorView
- States: loading (progress indicator), empty ('No products available'), error (message + Retry which invalidates productListProvider), success (at least 8 products, scrollable, reachable by vertical scroll)
- Stories: US-001

### SCR-02 ProductDetailScreen (`/products/:productId`)
Show product image, name, description, VAT-inclusive GBP price, variant selector and stock status of the selected variant, with an Add to cart button enabled only when an in-stock variant is selected; back via app-bar back button or system back returns to the list at the same scroll position.
- Components: AppBar with back button and CartBadgeButton, ProductImage, Product name (titleLarge), Description (bodyLarge), PriceText (priceLarge), VariantChoiceChips, StockStatusText, Add to cart FilledButton (minimum 48dp high, full width), LoadingView, ErrorView
- States: loading, not-found/error (ProductNotFound or load failure, message + Retry/back), success with variant selected (highlighted chip, stock status shown, Add to cart enabled if in stock), success with no variant selected (Add to cart disabled), variant out of stock (chip disabled, labelled '<size>, out of stock', cannot be selected or added), no selectable variant (all out of stock: shows 'Out of stock' and a disabled button), added to cart (cart badge count increases by 1, brief SnackBar confirmation)
- Stories: US-001, US-002, US-003

### SCR-03 CartScreen (`/cart`)
Optional in-memory cart: list lines with product name, variant, unit price and quantity, adjust quantity or remove, and show a GBP total computed from integer pence. No checkout or payment control in any state; the cart is empty after app relaunch.
- Components: AppBar with back button, ListView of CartLineTile, TotalRow, EmptyView with 'Browse products' button, ErrorView
- States: empty ('Your cart is empty' with 'Browse products' button to '/', no checkout or payment control), success (lines and 'Total £X.XX', updates immediately on increment, decrement or remove), decrement disabled at quantity 1 (use Remove), increment disabled at variant stock (maxQuantity), loading (not applicable; state is synchronous in memory), error (fallback ErrorView if state cannot be read)
- Stories: US-003

## Navigation
- SCR-01 ProductListScreen → SCR-02 ProductDetailScreen: Tap a ProductCard -> context.push('/products/<id>')
- SCR-02 ProductDetailScreen → SCR-01 ProductListScreen: App-bar back button or system back gesture (pop; list keeps same scroll position)
- SCR-01 ProductListScreen → SCR-03 CartScreen: Tap CartBadgeButton -> context.push('/cart')
- SCR-02 ProductDetailScreen → SCR-03 CartScreen: Tap CartBadgeButton -> context.push('/cart')
- SCR-03 CartScreen → SCR-02 ProductDetailScreen: App-bar back button or system back gesture (pop) when opened from detail
- SCR-03 CartScreen → SCR-01 ProductListScreen: App-bar back button or system back gesture (pop) when opened from list; or tap 'Browse products' in the empty state -> context.go('/')
- SCR-02 ProductDetailScreen → SCR-01 ProductListScreen: Retry/back on not-found error state -> pop or context.go('/')

## Accessibility
- Minimum touch target 48x48dp for all interactive elements: ProductCard, CartBadgeButton, variant ChoiceChips, quantity decrement/increment IconButtons, Remove button, Add to cart, Retry and Browse products buttons.
- Body text is at least 14sp (bodyMedium 14sp, bodyLarge 16sp); text scales with the system font size without clipping or overflow.
- All text and icon colours meet WCAG AA contrast in light and dark themes: at least 4.5:1 for normal text and 3:1 for large text and UI components.
- All images and icons have semantic labels (ProductImage uses the product name; icon-only buttons have tooltips/labels such as 'Cart, N items', 'Back', 'Decrease quantity of <name>', 'Increase quantity of <name>', 'Remove <name> from cart').
- Selected variant and stock status are not conveyed by colour alone: selected chips show a check icon plus highlight, and stock status uses an icon plus text (In stock / Low stock - only N left / Out of stock).
- Out-of-stock variant chips are disabled and announced as '<size>, out of stock' to screen readers.
- Disabled Add to cart, decrement and increment controls are exposed as disabled to TalkBack; the disabled colours still keep readable text.
- Cart total and quantity changes are announced through live-region semantics so screen readers hear updates.
- Loading, empty and error states have readable text and semantic labels; Retry buttons are reachable by focus order.
- Logical focus/reading order top to bottom on each screen; the back button is the first focusable element in the app bar.
- Light and dark themes are both supported from a single theme definition in lib/core/theme built from design tokens; no hard-coded colours or sizes in widgets.
- Prices are read as full amounts (e.g. '19 pounds 99') via semantic labels on PriceText.