# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #9C2F5B | #F2A7C3 |
| onPrimary | #FFFFFF | #4A0E27 |
| secondaryContainer | #F8D9E4 | #5C2440 |
| onSecondaryContainer | #3A0B20 | #FFD9E6 |
| background | #FFF9F8 | #141012 |
| surface | #FFFFFF | #1E181A |
| surfaceVariant | #F1E7E9 | #2A2225 |
| onSurface | #1F1A1B | #F3EDEE |
| onSurfaceVariant | #5E5457 | #CFC3C6 |
| outline | #8A7E81 | #9A8E91 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| success | #1E7B45 | #7FD9A1 |
| inverseSurface | #322F30 | #E9E0E1 |
| onInverseSurface | #F5EFF0 | #322F30 |
| imagePlaceholder | #F1E7E9 | #2A2225 |
| badge | #9C2F5B | #F2A7C3 |
| onBadge | #FFFFFF | #4A0E27 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineMedium | 24.0 | 700 | 1.33 |
| titleLarge | 20.0 | 600 | 1.4 |
| titleMedium | 16.0 | 600 | 1.5 |
| priceLarge | 22.0 | 700 | 1.27 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.43 |
| labelLarge | 14.0 | 600 | 1.43 |
| labelMedium | 12.0 | 500 | 1.33 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 24, 999 dp.

## Shared widgets
- **AppThemeTokens**: lib/core/theme: ThemeData (light and dark) built from the color, typography, spacing and radius tokens above. Widgets never hard-code colors or sizes; they read them from Theme/ThemeExtension.
- **ProductImage**: Network/asset image with cached loading, fixed aspect ratio (1:1 in cards, 4:3 in the detail carousel) and a neutral imagePlaceholder (icon on surfaceVariant) when the image is missing or fails to load, so the layout never breaks. Always has a semantic label (product name).
- **PriceText**: Formats Money (integer cents + USD) as $x.xx for display only (e.g. $24.00, $68.47). Uses priceLarge on detail and cart subtotal, titleMedium/labelLarge in cards and lines.
- **ProductCard**: Tappable card in the 2-column grid: ProductImage on top, then name (titleMedium, max 2 lines, ellipsis), brand (bodyMedium, onSurfaceVariant) and PriceText. Radius 12, surface color, full card is one 48dp+ tap target with a combined semantic label 'name, brand, price'.
- **CategoryFilterBar**: Horizontal scrollable row of exactly five choice chips: All, Skincare, Makeup, Haircare, Fragrance. Selected chip uses secondaryContainer with onSecondaryContainer text and a check icon; unselected chips use surface with an outline border. Chip height 48dp. Tapping the active category clears it to All. No search box or sort control.
- **CartIconButton**: App bar action with a shopping bag icon and an item-count badge (from cartItemCountProvider; badge hidden at 0, shows 99+ above 99). 48x48dp touch target, semantic label 'Cart, N items'. Navigates to /cart and is present on every screen except the Cart screen.
- **VariantSelector**: Single-select option group. Shade mode (variantType shade) renders circular color swatches (min 48dp hit area, selected ring in primary) with the shade name shown below; size mode (variantType size) renders choice chips (e.g. 30 ml, 50 ml). Exactly one option selectable. Not rendered when variantType is none. Each option has a semantic label and selected state. Reads/writes selectedVariantProvider(productId).
- **ImageCarousel**: PageView of ProductImage with dot page indicator for the larger detail image(s); shows a single placeholder when the product has no images. Swipeable, indicator dots are decorative (excluded from semantics) and the page is announced as 'Image 1 of N'.
- **PrimaryButton**: Full-width filled button (primary / onPrimary), height 52dp, radius 12, labelLarge text, disabled style using onSurface at 12% fill and 38% text opacity. Used for Add to Cart, Checkout and Browse products.
- **QuantityStepper**: Decrease (-) button, quantity text and increase (+) button, each button 48x48dp. Decrease is disabled at quantity 1, increase is disabled at 99. Semantic labels 'Decrease quantity of <name>' and 'Increase quantity of <name>'; quantity announced as a live value.
- **CartLineTile**: Cart row: 72dp ProductImage thumbnail, name, brand, variant label (e.g. 'Shade: Rose Petal' or 'Size: 50 ml') when present, unit price, QuantityStepper, line total and a Remove text button (48dp min). Only the affected line is removed on Remove.
- **SubtotalBar**: Bottom-pinned surface panel on the Cart screen with 'Subtotal' label, PriceText (sum of unitPrice.amountMinor * quantity in integer cents) and the Checkout PrimaryButton below it. Respects the safe-area bottom inset.
- **AsyncStateView**: Reusable wrapper around AsyncValue that renders consistent loading (skeleton/progress indicator with semantic label 'Loading'), empty (icon, message, optional action) and error (message plus 'Try again' retry button) layouts on all screens.
- **AppSnackbar**: Helper for floating snackbars using inverseSurface / onInverseSurface. Used for 'Added to cart', 'Please choose a size', 'Please choose a shade' and 'Checkout is coming soon. This is a demo.'. Duration 3 s, announced by screen readers.

## Screens
### SCR-01 Product List (`/`)
Home screen of the demo. Lets the shopper browse the whole sample catalog (about 24 products) in a scrollable 2-column grid showing image, name, brand and price in US dollars, and narrow it with the category filters All, Skincare, Makeup, Haircare and Fragrance. Tapping a card pushes the Product Detail screen (context.push) so back returns to the same scroll position. No search or sort control.
- Components: AppBar with brand logo/title and CartIconButton, CategoryFilterBar (All + 4 categories, selected chip highlighted, tap active chip again clears to All), GridView 2 columns with PageStorageKey to preserve scroll position, ProductCard, ProductImage (neutral placeholder when no image), PriceText, AsyncStateView
- States: loading (skeleton cards in the 2-column grid), success (grid of all products, or only the selected category), empty (filtered category has no products: 'No products in this category' with a 'Show all' action), error (message with retry button that reloads the catalog)
- Stories: US-001, US-002, US-004

### SCR-02 Product Detail (`/products/:productId`)
Shows one product in detail: larger image carousel, name, brand, price, description and, where they apply, a shade selector (makeup) or size selector (skincare/haircare/fragrance) with exactly one option selectable, plus the Add to Cart button. Adds quantity 1 of the chosen variant and confirms with a snackbar; if a selector is present and nothing is selected (and no default was preselected) nothing is added and 'Please choose a size' / 'Please choose a shade' is shown. No selector is shown when variantType is none and Add to Cart is enabled. Pushed on top of the list so back returns to the same scroll position.
- Components: AppBar with back button and CartIconButton, ImageCarousel, ProductImage, Product name (headlineMedium), brand (bodyMedium) and PriceText (priceLarge), Description text (bodyLarge), VariantSelector (shade swatches or size chips, hidden when variantType is none), PrimaryButton 'Add to Cart' pinned at the bottom, AppSnackbar (added confirmation and choose-a-variant message), AsyncStateView
- States: loading (image and text skeletons), success (product shown; selector shown per variantType; default variant preselected if isDefault), no-variants (no selector displayed, Add to Cart enabled), variant-required (nothing selected on Add to Cart: item not added, inline/snackbar message 'Please choose a size' or 'Please choose a shade'), added (snackbar 'Added to cart' and badge count updated), not-found (unknown product id: message with 'Back to products' action to '/'), error (message with retry button)
- Stories: US-003, US-004

### SCR-03 Cart (`/cart`)
Lets the shopper review the in-memory cart: each line shows image, name, brand, chosen size or shade, unit price, quantity stepper and line total, with a Remove action. Quantity is at least 1 (decrease disabled at 1) and at most 99 (increase disabled at 99). A running subtotal in US dollars is computed from integer cents (e.g. 1999 x 3 + 850 = $68.47). A Checkout button below the subtotal is a placeholder that shows 'Checkout is coming soon. This is a demo.' and keeps the user on the Cart screen with contents unchanged, with no payment screen, sign-in, order creation or network call. Empty cart shows a message and a 'Browse products' action, with no Checkout button.
- Components: AppBar with back button and title 'Cart', ListView of CartLineTile, QuantityStepper, ProductImage, PriceText, Remove text button per line, SubtotalBar, PrimaryButton 'Checkout' (placeholder), PrimaryButton 'Browse products' (empty state), AppSnackbar ('Checkout is coming soon. This is a demo.'), AsyncStateView
- States: loading (brief progress indicator while the screen builds; cart state itself is synchronous), success (one or more lines with subtotal and Checkout button), empty (icon and message 'Your cart is empty' with 'Browse products' action to '/'; Checkout not shown), quantity-limits (decrease disabled at 1, increase disabled at 99), checkout-placeholder (snackbar 'Checkout is coming soon. This is a demo.'; screen and cart unchanged), error (generic message with retry and a 'Browse products' action if the cart view fails to render)
- Stories: US-004, US-005, US-006

## Navigation
- SCR-01 → SCR-02: Tap a ProductCard (context.push('/products/:productId'); back returns to the list at the same scroll position)
- SCR-01 → SCR-03: Tap CartIconButton in the app bar (context.push('/cart'))
- SCR-02 → SCR-01: Tap app bar back button / system back gesture, or 'Back to products' on the not-found state
- SCR-02 → SCR-03: Tap CartIconButton in the app bar (context.push('/cart'))
- SCR-03 → SCR-01: Tap 'Browse products' on the empty cart state (context.go('/'))
- SCR-03 → SCR-02: Tap app bar back button / system back gesture when the cart was opened from Product Detail
- SCR-03 → SCR-01: Tap app bar back button / system back gesture when the cart was opened from Product List

## Accessibility
- All interactive controls (cards, chips, swatches, steppers, Remove, cart icon, buttons) have a minimum touch target of 48x48dp.
- Text contrast meets WCAG AA in light and dark themes: at least 4.5:1 for body text and 3:1 for large text, icons and component borders (e.g. onPrimary on primary, onSurface on surface, onSurfaceVariant on surface).
- Selected states (filter chip, shade swatch, size chip) are never conveyed by color alone: a check icon or ring plus a selected semantic state is also used.
- All images and icons have semantic labels (product name for images, 'Cart, N items' for the cart icon); purely decorative elements such as carousel dots are excluded from semantics.
- Shade swatches expose the shade name as their semantic label and announce selected/not selected.
- Quantity controls have descriptive labels ('Increase quantity of <name>'); disabled states are exposed to screen readers; quantity changes and subtotal updates are announced.
- Snackbar messages (added to cart, choose a size/shade, checkout coming soon) are announced by screen readers.
- Text respects the system font scale (up to at least 200%) without clipping: cards and lines use flexible heights and ellipsis after 2 lines.
- Typography line_height values are Flutter TextStyle height multipliers; minimum body text size is 14sp.
- Every screen provides visible loading, empty and error states with a clear retry or recovery action.
- Light and dark themes are both supported and follow the system setting; tokens come only from lib/core/theme.