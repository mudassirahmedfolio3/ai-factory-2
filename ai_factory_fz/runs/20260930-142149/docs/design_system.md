# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1A5FB4 | #A8C7FA |
| onPrimary | #FFFFFF | #062E6F |
| primaryContainer | #D6E4FF | #2A4373 |
| onPrimaryContainer | #0B2F66 | #D6E4FF |
| background | #FAFAF7 | #121316 |
| surface | #FFFFFF | #1C1D21 |
| surfaceVariant | #E8EAF0 | #2B2D33 |
| onSurface | #1B1B1F | #E4E2E6 |
| onSurfaceVariant | #5A5D66 | #C4C6D0 |
| outline | #767A85 | #8E919A |
| divider | #D9DBE1 | #3A3C43 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| errorContainer | #F9DEDC | #5C1A16 |
| onErrorContainer | #410E0B | #F9DEDC |
| success | #1B6E3A | #7FD99A |
| successContainer | #DDF3E4 | #12391F |
| warning | #8A4B00 | #FFB74D |
| warningContainer | #FFE8C7 | #4A2E00 |
| salePrice | #B3261E | #F2B8B5 |
| badgeBackground | #B3261E | #F2B8B5 |
| onBadge | #FFFFFF | #601410 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineMedium | 24.0 | 700 | 1.33 |
| titleLarge | 20.0 | 600 | 1.4 |
| titleMedium | 16.0 | 600 | 1.5 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.43 |
| labelLarge | 14.0 | 600 | 1.43 |
| labelMedium | 12.0 | 600 | 1.33 |
| priceLarge | 22.0 | 700 | 1.27 |
| priceMedium | 16.0 | 700 | 1.5 |
| priceStrike | 14.0 | 400 | 1.43 |

Spacing scale: 0, 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 0, 4, 8, 12, 16, 999 dp.

## Shared widgets
- **AppTheme (lib/core/theme)**: Builds light and dark ThemeData from the design tokens (colors, typography, spacing, corner radii). Widgets read tokens from the theme; no hard-coded colors or sizes in widgets. Text uses system font scaling.
- **ProductImage**: Lazily built image (bundled asset or placeholder) with a loading placeholder (surfaceVariant shimmer/progress) and an error placeholder icon so missing or failed loads never crash. Always has a semantic label from imageAltText.
- **StockStatusChip**: Chip reading In stock (success), Low stock (warning, 5 units or fewer) or Out of stock (error). Status is conveyed by text plus color, not color alone. Derived from domain StockStatus (0 = out_of_stock, 1..5 = low_stock, above 5 = in_stock).
- **PriceText**: Formats integer cents as USD (12999 shows $129.99). When a sale price is set, shows the sale price (salePrice color, priceMedium/priceLarge) and the original price struck through (priceStrike, onSurfaceVariant). Semantic label reads 'Sale price X, was Y'. No floating-point money.
- **CartBadgeButton**: App bar IconButton (48x48dp minimum) with a cart icon and a badge showing cartItemCountProvider (sum of quantities; hidden at 0). Semantic label 'Cart, N items'. Opens /cart via context.push.
- **ProductListRow**: Row for ProductSummary: ProductImage, name, PriceText from the default variant, StockStatusChip from summed variant stock. Whole row is tappable (minimum 48dp height, in practice 96dp) and calls context.go('/products/{id}'). Semantic label combines name, price and stock status.
- **VariantSelector**: ChoiceChips grouped by option name (for example finish, color_temperature). Each chip is at least 48dp tall, has a selected state (primaryContainer) and a semantic label 'option name: value, selected/not selected'. Selecting calls selectedVariantProvider.select(optionName, value).
- **QuantityStepper**: Minus button, quantity text and plus button, each button 48x48dp with semantic labels 'Decrease quantity' and 'Increase quantity'. Bounded 1..stockQuantity; buttons disable at the bounds. Used on the detail screen (detailQuantityProvider) and on cart lines (cartProvider.setQuantity).
- **SpecificationsSection**: Titled 'Specifications' section listing only the non-null fields of the merged specifications (variant overrides on top of product specifications) as label/value rows with units: W, lm, K, V, mm. Product-type-specific (for example wattage, lumens, color temperature, dimmable, bulb type for a bulb; material, finish, dimensions, IP rating for a fixture).
- **AvailabilityText**: Text plus StockStatusChip for the selected variant; reads Out of stock when stockQuantity is 0.
- **LoadingView**: Centered CircularProgressIndicator with semantic label 'Loading'. Used for full-screen loading states; list rows use ProductImage placeholders.
- **EmptyState**: Icon, message and optional action button (48dp minimum height). Used for 'No products available' and 'Your cart is empty' with a Browse products action.
- **ErrorState**: Icon, error message and a Retry button (48dp minimum height) that calls the provider's refresh/invalidate. Also used inline at the end of the list for a load-more error.
- **CartLineTile**: Cart line with ProductImage, product name, variant name, unit price, line total, QuantityStepper and a Remove action (48x48dp, semantic label 'Remove <product name>').
- **CartSummary**: Summary section with Subtotal, Tax, Shipping ('Free' when subtotal is $150.00 or more, otherwise $9.99) and Total, all tax-exclusive prices formatted from integer cents. No checkout, sign-in or payment control.

## Screens
### SCR-01 ProductListScreen (`/products`)
Initial location of the app. Shows a scrollable, paginated-style list of lighting products loaded from the local mock catalog without any sign-in, so the Homeowner shopper can quickly browse image, name, effective price, sale price with struck-through original, and stock status, and tap a row to open its details. Page size is kCatalogPageSize = 10; the next page loads when the user scrolls within 3 rows of the end. ListView.builder uses a PageStorageKey so scroll position is preserved when returning from detail.
- Components: AppBar with title and CartBadgeButton, ListView.builder (PageStorageKey) of ProductListRow, ProductImage (lazy, loading and error placeholders), PriceText, StockStatusChip, LoadingView, EmptyState, ErrorState, Load-more footer (progress indicator or inline ErrorState with Retry)
- States: loading (LoadingView while page 1 loads), empty ('No products available'), error (message with Retry), success (list of product rows), loading-more (footer progress indicator while the next page loads), load-more-error (inline message with Retry, existing rows kept), image-loading (per-row placeholder until the image is ready), image-error (per-row placeholder icon)
- Stories: US-001

### SCR-02 ProductDetailScreen (`/products/:productId`)
Child route of /products. Lets the Project buyer view the selected variant image, name, brand, selected variant SKU, price and sale price, description, availability and a Specifications section, switch variants (price, image, SKU, availability and specifications update), choose a quantity and add the in-stock variant to the in-memory cart. Back returns to the list at the same scroll position.
- Components: AppBar with back control and CartBadgeButton, ProductImage (selected variant image), Name, brand and SKU text, PriceText, AvailabilityText and StockStatusChip, Description text, VariantSelector (ChoiceChips grouped by option name), SpecificationsSection, QuantityStepper (bounded 1..stockQuantity), Add to cart button (48dp minimum height), LoadingView, ErrorState
- States: loading (LoadingView while productDetailProvider resolves), error (message with Retry), not-found (product id does not exist, message with a Back to products action), success (all product details shown), variant out of stock (availability reads Out of stock, QuantityStepper and Add to cart control disabled), variant low stock (Low stock chip, quantity capped at available stock), image-error (placeholder icon), added-to-cart confirmation (SnackBar and cart badge count updates)
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Optional in-memory cart (dropped first if it delays M1). Opened via context.push from the app bar cart badge on list and detail. Lets the Homeowner shopper review lines, change quantities (1..stockQuantity), remove items, and see Subtotal, Tax, Shipping (Free at $150.00 or more) and Total computed from integer cents. Cart is empty after relaunch. No checkout, sign-in or payment control.
- Components: AppBar with back control and title 'Cart', CartLineTile list (image, product name, variant name, unit price, line total), QuantityStepper, Remove action, CartSummary (Subtotal, Tax, Shipping or 'Free', Total), EmptyState ('Your cart is empty' with Browse products action)
- States: empty ('Your cart is empty' with Browse products action), success (lines and summary shown, totals recalculated on every change), quantity at stock limit (increase button disabled), free shipping (Shipping shows 'Free' when subtotal is at least $150.00), image-error (placeholder icon)
- Stories: US-003

## Navigation
- App launch → SCR-01 ProductListScreen: App opens at initial location /products (no sign-in prompt)
- SCR-01 ProductListScreen → SCR-02 ProductDetailScreen: Tap a product row: context.go('/products/{id}')
- SCR-02 ProductDetailScreen → SCR-01 ProductListScreen: Back control or system back; list stays mounted beneath (child route) so scroll position is preserved
- SCR-01 ProductListScreen → SCR-03 CartScreen: Tap CartBadgeButton in the app bar: context.push('/cart')
- SCR-02 ProductDetailScreen → SCR-03 CartScreen: Tap CartBadgeButton in the app bar: context.push('/cart')
- SCR-03 CartScreen → SCR-01 ProductListScreen: Tap Browse products in the empty state: context.go('/products')
- SCR-03 CartScreen → Previous screen (SCR-01 or SCR-02): Back control or system back (pop)
- SCR-02 ProductDetailScreen → SCR-01 ProductListScreen: Tap Back to products in the not-found state: context.go('/products')

## Accessibility
- Minimum touch target 48x48dp for all interactive elements: product rows, cart badge button, variant ChoiceChips, quantity stepper buttons, Remove action, Add to cart, Retry and Browse products buttons.
- Text contrast meets WCAG AA (at least 4.5:1 for body text, 3:1 for large text and non-text UI) in both light and dark themes; token pairs such as onSurface on surface, onPrimary on primary, success/warning/error on their containers and salePrice on surface were chosen to satisfy this.
- Text respects system font scaling (no fixed-height text containers); layouts wrap or grow rather than clip at large scales.
- All images and icons have semantic labels: product images use imageAltText, decorative images are excluded from semantics, the cart icon reads 'Cart, N items', placeholder icons have labels such as 'Image unavailable'.
- Stock status is conveyed by text (In stock, Low stock, Out of stock) and not by color alone.
- Sale price semantics read 'Sale price X, was Y'; the struck-through original price is never the only indicator of a sale.
- Variant ChoiceChips expose selected state and 'option name: value' labels to screen readers; QuantityStepper buttons are labelled 'Decrease quantity' and 'Increase quantity' and announce the new quantity.
- Disabled Add to cart and stepper controls expose disabled state to assistive technologies, and the Out of stock reason is visible in text.
- Loading, empty and error states are announced with semantic labels; error states always offer a Retry action.
- No hard-coded colors or sizes in widgets; light and dark themes are both supported through tokens in lib/core/theme.
- Focus and reading order follow visual order top to bottom; the back control is the first focusable element on detail and cart screens.