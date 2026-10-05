# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #8C3B4F | #F2B8C6 |
| onPrimary | #FFFFFF | #4A1425 |
| primaryContainer | #F8E1E7 | #5E2537 |
| onPrimaryContainer | #3F1220 | #FFD9E2 |
| background | #FFFBF9 | #1A1416 |
| surface | #FFFFFF | #251D20 |
| onSurface | #211A1C | #F5EDEF |
| onSurfaceVariant | #6B5C61 | #C9BCC0 |
| outline | #857378 | #9A8B90 |
| placeholder | #EFE6E8 | #3A2F33 |
| skeleton | #F1E8EA | #33292C |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| inverseSurface | #2E2427 | #F0E4E7 |
| onInverseSurface | #F8EEF0 | #2E2427 |
| badge | #8C3B4F | #F2B8C6 |
| onBadge | #FFFFFF | #4A1425 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| headlineLarge | 28.0 | 600 | 1.29 |
| headlineMedium | 22.0 | 600 | 1.27 |
| titleLarge | 18.0 | 600 | 1.33 |
| titleMedium | 16.0 | 600 | 1.5 |
| priceLarge | 22.0 | 700 | 1.27 |
| bodyLarge | 16.0 | 400 | 1.5 |
| bodyMedium | 14.0 | 400 | 1.43 |
| labelLarge | 14.0 | 600 | 1.43 |
| caption | 14.0 | 400 | 1.43 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 8, 12, 16, 24, 999 dp.

## Shared widgets
- **AppLogoBar**: Shared app bar showing the business logo (semantic label 'beauty-mvp logo') with a CartBadgeButton action. Used on Browse and Cart. Product Detail uses a back control plus the CartBadgeButton. Colors and sizes come from theme tokens in lib/core/theme.
- **CartBadgeButton**: 48x48dp cart icon button with a badge showing total units from cartItemCountProvider (badge hidden at 0). Semantic label 'Cart, N items'. Navigates to /cart.
- **CategoryChipRow**: Horizontally scrollable row of ChoiceChips: All, Skincare, Makeup, Haircare, Fragrance. All is selected by default; the selected chip uses primaryContainer fill, primary outline and a check icon so selection is not conveyed by color alone. Each chip has a minimum 48dp height and reads/writes selectedCategoryProvider. Semantic label '<name>, selected' or '<name>'.
- **ProductTile**: Grid tile for a product: ProductImage (1:1 with placeholder), name (max 2 lines), brand, and PriceText. Whole tile is one 48dp+ tap target that opens /products/:productId. Semantic label '<name>, <brand>, <price>'. Name, brand and price stay visible when the image fails.
- **ProductImage**: Bundled asset image with a placeholder block (placeholder token plus neutral image icon) shown while loading and on error; never throws or blocks scrolling. Semantic label taken from image.alt; the decorative placeholder is excluded from semantics.
- **PriceText**: Formats Money (integer cents, USD) as dollars, e.g. $24.50, using integer arithmetic only. Semantic label reads as spoken price.
- **QuantitySelector**: Stepper for values 1-10 with decrease and increase 48x48dp buttons and a centered value. Decrease disabled at 1 and increase disabled at 10. Semantic labels 'Decrease quantity of <name>', 'Increase quantity of <name>', and value 'Quantity, N'. Used on Product Detail (productQuantityProvider) and in CartLineTile (cartProvider.setQuantity).
- **CartLineTile**: Cart row with ProductImage thumbnail, name, brand, unit price, QuantitySelector, line subtotal (unit price x quantity in integer cents) and a 48dp Remove button labelled 'Remove <name>'. Layout wraps vertically so it does not overflow at 150% text scale.
- **CartTotalRow**: Last element of the cart list: label 'Total' and the overall USD total from cartTotalProvider. Nothing appears below it (no checkout, payment, promo, shipping or tax element).
- **SkeletonTile**: Loading placeholder for ProductTile (image block, two text bars) using the skeleton token; used in the Browse loading grid and as a Cart/Detail loading placeholder.
- **EmptyState**: Centered icon, title, optional message and one primary action button (48dp min height). Used for 'No products in this category' (Show all) and 'Your cart is empty' (Browse products).
- **ErrorState**: Centered friendly message with an icon and a primary action button: Retry (invalidates catalogProvider) on Browse and Cart; 'Back to Browse' on Product Detail error and not-found. Message announced to screen readers as a live region.
- **AppSnackBar**: Floating SnackBar using inverseSurface tokens for add-to-cart confirmation ('<name> added to cart') and the cap message 'Maximum 10 per item'. Announced to screen readers.
- **PrimaryButton**: Full-width filled button, min height 48dp, radius 12, primary/onPrimary tokens, labelLarge text. Used for Add to Cart and state actions.

## Screens
### SCR-01 Browse (`/`)
Home screen. Lets the shopper scroll the whole bundled catalog in a 2-column grid and filter it by category (All, Skincare, Makeup, Haircare, Fragrance). The selected category is kept in selectedCategoryProvider (above the router) so it survives opening Detail and returning; grid scroll position is preserved with a PageStorageKey and Browse staying mounted under Detail. No search or sort controls.
- Components: AppLogoBar, CartBadgeButton, CategoryChipRow, SliverGrid (2 columns) of ProductTile, ProductImage, PriceText, SkeletonTile, EmptyState, ErrorState
- States: loading: skeleton tiles (SkeletonTile grid) while catalogProvider resolves, success: grid shows every product in catalog order for the selected category; All selected by default, empty: 'No products in this category' with a Show all action that sets the filter to All, error: friendly message with Retry button that invalidates catalogProvider (no blank screen or crash), image loading/failed: placeholder in the image area while name, brand and price remain visible
- Stories: US-001, US-002, US-006

### SCR-02 Product Detail (`/products/:productId`)
Shows one product clearly (large image, name, brand, price, short description, Key ingredients and/or How to use) and lets the shopper choose a quantity 1-10 and add it to the cart. Pushed on top of Browse so back returns to the same scroll position and category filter. No stock, variants, reviews or wishlist.
- Components: AppBar with back control and CartBadgeButton, ProductImage (large, semantic label from image.alt), Name, brand and PriceText, Short description, 'Key ingredients' and/or 'How to use' sections, QuantitySelector (starts at 1, decrease disabled at 1, increase disabled at 10), PrimaryButton 'Add to Cart' (full width), AppSnackBar, SkeletonTile, ErrorState
- States: loading: skeleton placeholders while catalogProvider resolves, with a Back to Browse action, success: full product content with quantity selector reset to 1 on each open, added: SnackBar confirmation and cart badge updates to the new total units, capped: when the merge exceeds 10 the line is capped at 10 and SnackBar shows 'Maximum 10 per item', error: friendly message with Back to Browse action, not-found: unknown productId shows 'Product not found' with Back to Browse action, image loading/failed: placeholder shown, rest of the content remains usable
- Stories: US-003, US-004, US-006

### SCR-03 Cart (`/cart`)
Lets the shopper review cart lines, change quantity (1-10), remove lines and see line subtotals and the overall USD total. The screen ends at the total: no checkout, payment, promo code, shipping or tax element. Cart is in memory only and unchanged while navigating; empty after the app is fully closed and reopened.
- Components: AppLogoBar (with back control), List of CartLineTile, QuantitySelector, ProductImage, PriceText, Remove button labelled 'Remove <name>', CartTotalRow (last element), SkeletonTile, EmptyState, ErrorState
- States: loading: skeleton lines while the catalog resolves (cart lines look up product data from the catalog), success: lines with image, name, brand, unit price, quantity, line subtotal and overall Total; subtotals and total update immediately on quantity change or removal, empty: 'Your cart is empty' with a Browse products action navigating to '/'; no total displayed, error: friendly message with Retry button that invalidates catalogProvider, image loading/failed: placeholder shown while text and prices remain visible
- Stories: US-005, US-004, US-006

## Navigation
- SCR-01 → SCR-02: Tap a ProductTile (context.push('/products/:productId')); Browse stays mounted underneath
- SCR-01 → SCR-03: Tap CartBadgeButton in the app bar (context.push('/cart'))
- SCR-02 → SCR-01: App bar back control or system back gesture (pop): returns to the same scroll position and category filter
- SCR-02 → SCR-01: Back to Browse action on the Detail loading, error or not-found state (context.go('/'))
- SCR-02 → SCR-03: Tap CartBadgeButton in the app bar (context.push('/cart'))
- SCR-03 → SCR-01: Browse products action on the empty-cart state (context.go('/'))
- SCR-03 → SCR-01: App bar back control or system back gesture when Cart was opened from Browse (pop)
- SCR-03 → SCR-02: App bar back control or system back gesture when Cart was opened from Product Detail (pop); cart contents unchanged

## Accessibility
- Minimum touch target 48x48dp for every interactive control: cart icon, category chips, ProductTile, quantity decrease/increase buttons, Remove button, Add to Cart button, back control and state action buttons.
- Body text at least 14sp everywhere (bodyMedium, labelLarge and caption are 14sp); text sizes are always scaled with the system text scale.
- Text/background contrast at least 4.5:1 (WCAG AA) in both light and dark themes for all text tokens (onSurface, onSurfaceVariant, onPrimary on primary, onError on error, onInverseSurface on inverseSurface); outline and control boundaries at least 3:1.
- Layouts must remain usable at 150% system text scale on Browse, Product Detail and Cart: product name, price, quantity and the Add to Cart button stay readable with no overlap, clipping or overflow (allow name wrap to 2+ lines, avoid fixed-height text containers, CartLineTile wraps vertically, Detail content scrolls).
- All images have semantic labels: product images use image.alt, the logo is labelled 'beauty-mvp logo'; decorative placeholders are excluded from semantics.
- All icon buttons have semantic labels: 'Cart, N items', 'Decrease quantity of <name>', 'Increase quantity of <name>', 'Remove <name>', 'Back'.
- Disabled states are exposed to screen readers: decrease disabled at 1 and increase disabled at 10 (onPressed null), with visible reduced emphasis that still meets non-text contrast for the icon outline.
- Selected category chip is conveyed by more than color (check icon, filled container, outline) and by semantics 'selected'.
- SnackBar confirmations, cap messages and error messages are announced to screen readers (live region / SnackBar semantics).
- Badge count is part of the cart button semantic label and is not read separately.
- Colors, sizes and spacing come only from design tokens in lib/core/theme with light and dark themes following the system setting; no hard-coded values in widgets.
- Portrait phone layout only; logical focus and reading order follow visual order (app bar, filter, grid; image, name, brand, price, description, sections, quantity, Add to Cart).
- Prices are read as spoken dollars (e.g. 'twenty-four dollars fifty cents') and computed from integer cents with no floating-point rounding.