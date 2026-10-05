# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #7A4F00 | #FFC857 |
| onPrimary | #FFFFFF | #2B1B00 |
| primaryContainer | #FFE7B8 | #5C3B00 |
| onPrimaryContainer | #2B1B00 | #FFE7B8 |
| secondary | #3F4A5A | #B8C4D6 |
| onSecondary | #FFFFFF | #1B2431 |
| background | #FFFBF5 | #121212 |
| onBackground | #1C1B1A | #EDE9E3 |
| surface | #FFFFFF | #1E1E1E |
| onSurface | #1C1B1A | #EDE9E3 |
| surfaceVariant | #F1EBE1 | #2A2926 |
| onSurfaceVariant | #5F5A52 | #B9B3A8 |
| outline | #7D766B | #958F84 |
| divider | #E3DCCF | #3A3833 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| stockInStock | #1B6E3A | #7EDC9A |
| stockLow | #8F4B00 | #FFB74D |
| stockOut | #B3261E | #F2B8B5 |
| salePrice | #B3261E | #FFB4AB |
| originalPriceStruck | #5F5A52 | #B9B3A8 |
| disabledContainer | #E0DBD2 | #3A3833 |
| onDisabled | #5F5A52 | #B9B3A8 |
| snackbarBackground | #322F2B | #EDE9E3 |
| onSnackbar | #FFFFFF | #1C1B1A |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineSmall | 24.0 | 700 | 1.33 |
| titleLarge | 20.0 | 600 | 1.4 |
| titleMedium | 16.0 | 600 | 1.5 |
| priceLarge | 22.0 | 700 | 1.27 |
| priceMedium | 16.0 | 700 | 1.5 |
| priceStruck | 14.0 | 400 | 1.43 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.43 |
| labelLarge | 14.0 | 600 | 1.43 |
| labelSmall | 12.0 | 500 | 1.33 |

Spacing scale: 0, 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 28 dp.

## Shared widgets
- **AppTheme (lib/core/theme)**: Builds light and dark ThemeData from the color, typography, spacing and corner radius tokens using ColorScheme and TextTheme extensions. No hard-coded colors or sizes in widgets. Text uses the system font scale (no clamping below 1.0). Material 3 enabled and ThemeMode follows the system.
- **LoadingView**: Centered CircularProgressIndicator with a Semantics label 'Loading'. Used by every AsyncValue.loading branch. The list screen may show skeleton cards, but the semantic label stays the same.
- **EmptyView**: Centered icon, title (titleMedium) and optional message plus optional action button (min 48dp). Product list uses the message 'No products available'. Cart uses 'Your cart is empty' with a 'Browse products' button. The icon has a semantic label.
- **ErrorView**: Centered error icon (semantic label 'Error'), message text and a 'Retry' FilledButton (min 48dp) that invalidates the screen's provider. Also used for the 'Product not found' state, where the retry is replaced by a 'Back to products' button.
- **CartBadgeButton**: IconButton (shopping cart icon, 48x48dp minimum) in the AppBar of list and detail screens. Watches cartProvider.select((s) => s.itemCount) and shows a Badge with the count when greater than 0 (99+ cap). Semantics label: 'Cart, N items'. Tap calls context.pushNamed('cart').
- **ProductCard**: Card with InkWell (min height 48dp, whole card tappable) containing ProductImage thumbnail, name, brand, PriceText and StockStatusChip. Wrapped in Semantics with a single label combining name, price and stock status. Opens detail with context.pushNamed('productDetail', pathParameters: {'productId': id}).
- **ProductImage**: Image.asset with cacheWidth set so only visible rows decode (lazy), BoxFit.cover, fixed aspect ratio, errorBuilder placeholder icon on surfaceVariant. Always has a semanticLabel from the imageAlt text.
- **PriceText**: Formats integer pence as GBP (for example £24.99) using a single formatter in lib/core; never floats for money. When a sale price is present it shows the sale price (salePrice color, priceMedium/priceLarge) and the original price struck through (originalPriceStruck color, priceStruck). Semantics label reads 'Now £X, was £Y'. Prices include 20% VAT.
- **StockStatusChip**: Chip-style label with icon plus text (never color only): 'In stock' (stockInStock), 'Low stock' when quantity is 5 or fewer (stockLow, global threshold 5), 'Out of stock' (stockOut). Uses labelSmall/labelLarge with WCAG AA contrast.
- **QuantitySelector**: Row with minus IconButton, current quantity text and plus IconButton, each at least 48x48dp, with semantic labels 'Decrease quantity' and 'Increase quantity'. Range 1 to stockQuantity on the detail screen (state via StateProvider.autoDispose.family keyed by productId). On the cart screen it edits the line quantity via cartProvider.setQuantity, and the plus button at the max shows the cap SnackBar. Buttons disabled at bounds.
- **SpecRow**: Label and value row for the specifications section (label in onSurfaceVariant bodyMedium, value in onSurface bodyLarge, divider below). Only non-null spec fields are rendered, in fixed order: wattage, lumens, color temperature, voltage, light type, dimmable, material, finish, dimensions, weight, IP rating, bulb type, bulb included. Merged into one Semantics node 'label: value'.
- **CartLineTile**: Cart row with thumbnail ProductImage, name, unit price, QuantitySelector, line total and a remove IconButton (48x48dp, label 'Remove <name> from cart'). Line total is unitPriceMinor * quantity in integer pence.
- **CartSummaryBar**: Bottom bar on the Cart screen showing 'Subtotal' and the subtotal in GBP (sum of line totals, includes 20% VAT note 'Prices include VAT'). No checkout button in this demo.
- **AppSnackBar helpers**: Floating SnackBar helpers using snackbarBackground/onSnackbar tokens: add-to-cart confirmation with a 'View cart' action, and the cap message 'Only N in stock - quantity limited to N'. Announced to screen readers as a live region.

## Screens
### SCR-01 Product List (`/`)
Launch screen. Browse the bundled mock catalog (10 or more lighting products across categories) as a scrollable list showing image, name, price (with struck-through original and sale price when on sale) and stock status. Tapping a card opens Product Detail. Scroll position is kept when returning from detail.
- Components: AppBar (title 'Lighting', CartBadgeButton), ListView.builder with PageStorageKey, ProductCard, ProductImage (Image.asset with cacheWidth, lazy), PriceText, StockStatusChip, LoadingView, EmptyView, ErrorView
- States: loading (LoadingView while productListProvider resolves), empty (EmptyView 'No products available'), error (ErrorView with Retry that invalidates productListProvider), success (list of ProductCards; in stock, low stock (5 or fewer), out of stock and sale price variants)
- Stories: US-001

### SCR-02 Product Detail (`/products/:productId`)
Show the full product: image, name, SKU, brand, price (and sale price if applicable), description, stock status, quantity selector and lighting specifications (label/value pairs, only applicable ones). Add to cart adds the selected quantity to the in-memory cart, shows a confirmation SnackBar and updates the cart badge. Add to cart is disabled when out of stock. Back returns to the list at the same scroll position.
- Components: AppBar (back button, product name, CartBadgeButton), ProductImage, PriceText, StockStatusChip, Text: SKU, brand, description, QuantitySelector (1 to stockQuantity), FilledButton 'Add to cart' (min 48dp, disabled when out of stock), Specifications section with SpecRow list, AppSnackBar helpers, LoadingView, ErrorView
- States: loading (LoadingView while productDetailProvider(productId) resolves), error (ErrorView with Retry that invalidates productDetailProvider(productId)), not found (unknown productId shows 'Product not found' with a 'Back to products' button), success in stock (quantity selector and enabled Add to cart), success low stock (Low stock label, quantity capped at stockQuantity), success out of stock (Out of stock label, Add to cart disabled, quantity selector disabled), added (confirmation SnackBar with 'View cart' action and updated badge), capped (SnackBar 'Only N in stock - quantity limited to N')
- Stories: US-002, US-003

### SCR-03 Cart (`/cart`)
Optional in-memory cart (may be cut first if delivery is at risk). Lists each line with product name, unit price, quantity and line total, lets the shopper change quantity (capped at available stock with a message) or remove a line, and shows the subtotal in GBP computed with integer pence. Empty state when there are no lines. Cart is not persisted, so a relaunch starts empty.
- Components: AppBar (back button, title 'Cart'), ListView of CartLineTile, QuantitySelector, CartSummaryBar (subtotal), PriceText, AppSnackBar helpers (cap message), EmptyView ('Your cart is empty' with 'Browse products' button), LoadingView, ErrorView
- States: loading (LoadingView only if a provider is async; cartProvider is synchronous in-memory so this resolves immediately), empty (EmptyView shown when there are no lines, including after removing the last item), error (ErrorView fallback with Retry that invalidates cartProvider; not expected for the in-memory cart), success (lines with updated line totals and subtotal immediately after quantity change or removal), capped (SnackBar 'Only N in stock - quantity limited to N' when the requested quantity exceeds maxQuantity)
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap a ProductCard: context.pushNamed('productDetail', pathParameters: {'productId': id}) so the list keeps its scroll position
- SCR-02 → SCR-01: System back button or AppBar back control (pop returns to the list at the same scroll position); 'Back to products' button on the Product not found state
- SCR-01 → SCR-03: Tap CartBadgeButton in the AppBar: context.pushNamed('cart')
- SCR-02 → SCR-03: Tap CartBadgeButton in the AppBar or the 'View cart' action on the add-to-cart confirmation SnackBar: context.pushNamed('cart')
- SCR-03 → SCR-01: 'Browse products' button on the empty cart state: context.go('/'); back button pops to the previous screen

## Accessibility
- Minimum touch target 48x48dp for all tappable elements: product cards, CartBadgeButton, quantity plus/minus buttons, remove button, Add to cart, Retry and Browse products buttons.
- Text contrast meets WCAG AA in both light and dark themes (at least 4.5:1 for body text, 3:1 for large text and UI components); all color tokens are chosen for this and stock status is never conveyed by color alone (icon plus text label).
- Text respects the system font scale; layouts use flexible sizing and wrap or scroll rather than clip at large font scales.
- All images and icons have semantic labels (product images use the imageAlt text; decorative icons are excluded from semantics); ProductImage placeholder on error also has a label.
- Each ProductCard exposes a single Semantics label combining name, price and stock status (for example 'Name, £24.99, In stock'); sale prices read 'Now £X, was £Y'.
- SpecRow items are merged into one node 'label: value' so screen readers read them as pairs; Specifications section heading is marked as a header.
- Disabled Add to cart on out-of-stock products is exposed as disabled to assistive tech and the reason (Out of stock) is visible text next to it.
- CartBadgeButton announces 'Cart, N items'; SnackBars (add-to-cart confirmation and stock cap message) are announced as live regions.
- Loading, empty and error states are exposed with semantic labels; ErrorView Retry is focusable and labelled.
- Focus and reading order follow visual order top to bottom; back navigation available via both system back and AppBar back control.
- Supports light and dark themes following the system setting; no hard-coded colors or sizes in widgets, all values come from theme tokens.