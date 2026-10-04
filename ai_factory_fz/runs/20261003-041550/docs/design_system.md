# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #0B6E4F | #3DDC97 |
| onPrimary | #FFFFFF | #003822 |
| secondary | #1F3A5F | #9BB4D4 |
| onSecondary | #FFFFFF | #0A1A2E |
| background | #F7F8FA | #121417 |
| surface | #FFFFFF | #1C1F24 |
| onSurface | #1A1C1E | #E3E5E8 |
| onSurfaceVariant | #5C636A | #A8ADB4 |
| outline | #D0D5DB | #3A4048 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| success | #1B7A4E | #6FCF97 |
| warning | #9A6700 | #F0C14B |
| price | #0B6E4F | #3DDC97 |
| disabled | #9AA0A6 | #5F6368 |
| imagePlaceholder | #E8EAED | #2A2E34 |
| badgeBackground | #0B6E4F | #3DDC97 |
| badgeForeground | #FFFFFF | #003822 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| displayLarge | 32.0 | 700 | 40.0 |
| headlineMedium | 24.0 | 600 | 32.0 |
| titleLarge | 20.0 | 600 | 28.0 |
| titleMedium | 16.0 | 600 | 24.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| labelLarge | 14.0 | 600 | 20.0 |
| labelSmall | 12.0 | 500 | 16.0 |
| priceLarge | 22.0 | 700 | 28.0 |
| priceMedium | 16.0 | 700 | 24.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48 dp. Corner radii: 0, 4, 8, 12, 16, 24 dp.

## Shared widgets
- **AppScaffold**: Standard screen shell with themed AppBar, optional cart action (icon + badge of in-memory cart item count), and SafeArea body. AppBar title uses titleLarge; back affordance shown when canPop.
- **ProductListTile**: Tappable catalog row (min height 72dp, full-width hit target ≥48dp). Shows 64×64 primary image or ImagePlaceholder, product name (titleMedium, max 2 lines), formatted USD price from integer cents (priceMedium), and optional stock hint. Semantics: button labeled with product name and price.
- **PriceText**: Formats integer minor units (cents) + ISO 4217 USD as display string (e.g. $12.99) using integer division/modulo only—never floating-point. Applies price color token and given type style.
- **ImagePlaceholder**: Neutral surface for missing product photos; uses imagePlaceholder color, corner radius 8, and Semantics label describing the product or 'Product image unavailable'.
- **ProductImageCarousel**: Horizontal PageView of product photos with page indicator; each image has a semantic label. Falls back to ImagePlaceholder when the mock catalog has no URLs.
- **VariantChipGroup**: Wrap of selectable variant chips (min 48×48 touch target). Selected uses primary/onPrimary; unavailable variants use disabled styling, are not selectable, and announce 'Out of stock' via Semantics.
- **StockStatusLabel**: Shows availability for the selected variant: 'In stock' (success), 'Only N left' (warning when low), or 'Out of stock' (error). Uses labelLarge and live region for screen readers when selection changes.
- **PrimaryButton**: Filled CTA with min height 48dp, horizontal padding 24, corner radius 12. Uses primary/onPrimary. Disabled when selected variant has zero stock or action blocked; Semantics button with explicit label.
- **CartLineItem**: Cart row showing product name, variant label, unit PriceText (cents/USD), quantity, and line total (unitPriceCents × quantity, integer math). Min touch target 48dp for any quantity controls if present.
- **CartBadgeIcon**: AppBar cart icon with optional numeric badge when CartState has items. Semantic label 'Cart, N items' or 'Cart, empty'. Opens /cart.
- **AsyncStateView**: Reusable wrapper for Riverpod AsyncValue: CircularProgressIndicator for loading; EmptyState for empty lists; ErrorState with message and Retry; child builder for data.
- **EmptyState**: Centered illustration or icon, title (titleLarge), supporting bodyMedium copy, optional PrimaryButton. Used when mock catalog is empty or cart has no lines.
- **ErrorState**: Centered error icon, title, body message (onSurface), and PrimaryButton 'Retry' (≥48dp) that re-invokes the AsyncNotifier load from local/mock catalog.
- **LoadingSkeletonList**: 3–5 shimmer product-row placeholders matching ProductListTile layout for catalog loading; announce 'Loading products' via Semantics.

## Screens
### SCR-01 ProductListScreen (`/products`)
Browse the local/mock product catalog without sign-in. Landing screen after app launch. Each row shows name, USD price from integer cents, and primary image or placeholder. Scrolls entirely from in-app mock data—no live API. Cart badge opens the in-memory cart.
- Components: AppScaffold, CartBadgeIcon, AsyncStateView, LoadingSkeletonList, EmptyState, ErrorState, ProductListTile, PriceText, ImagePlaceholder
- States: loading, empty, error, success
- Stories: US-001

### SCR-02 ProductDetailScreen (`/products/:productId`)
Show one product from the mock catalog: name, description, photos or placeholder, price in USD from integer cents, selectable variants with per-variant stock, and Add to cart for in-stock variants. System/in-app back returns to product list without losing catalog scroll context when possible.
- Components: AppScaffold, CartBadgeIcon, AsyncStateView, EmptyState, ErrorState, ProductImageCarousel, ImagePlaceholder, PriceText, VariantChipGroup, StockStatusLabel, PrimaryButton
- States: loading, empty, error, success, variantOutOfStock
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Simple in-memory cart preview: each line shows name, variant, quantity, unit price (cents/USD), and line total via integer math. Not persisted across process restart. No checkout or payment. Empty state when cart has no items.
- Components: AppScaffold, AsyncStateView, EmptyState, CartLineItem, PriceText, PrimaryButton
- States: empty, success
- Stories: US-003

## Navigation
- app_launch → SCR-01: App start; go_router initialLocation /products; mock catalog AsyncNotifier begins load
- SCR-01 → SCR-02: Tap ProductListTile; context.push('/products/:productId')
- SCR-02 → SCR-01: System back or AppBar back; context.pop() restores product list
- SCR-01 → SCR-03: Tap CartBadgeIcon; context.push('/cart')
- SCR-02 → SCR-03: Tap CartBadgeIcon or optional post-add snackbar action 'View cart'; context.push('/cart')
- SCR-03 → SCR-01: System/AppBar back when cart opened from list; or EmptyState CTA 'Browse products' → go('/products')
- SCR-03 → SCR-02: System/AppBar back when cart opened from detail; context.pop()
- SCR-02 → SCR-02: Add to cart on in-stock variant updates CartNotifier in place; stay on detail; snackbar confirms add

## Accessibility
- Minimum touch target 48×48 dp for ProductListTile, VariantChipGroup chips, PrimaryButton, CartBadgeIcon, Retry, and all tappable AppBar actions.
- Text and icon contrast meets WCAG AA: onSurface on background/surface ≥4.5:1; primary buttons use onPrimary on primary ≥4.5:1 in light and dark themes.
- All product images and ImagePlaceholder expose Semantics labels (product name + 'photo' or 'image unavailable').
- PriceText is announced as spoken currency (e.g. 'twelve dollars and ninety-nine cents') where feasible; never expose raw cents alone without currency context.
- Unavailable variants are not focusable as selected actions; Semantics announce 'Out of stock' and StockStatusLabel updates as a live region on variant change.
- Loading states announce 'Loading products' / 'Loading product details'; empty and error states use headings and actionable Retry / Browse with clear labels.
- CartBadgeIcon semantic label includes item count; cart lines announce name, variant, quantity, unit price, and line total.
- No auth gates, password fields, or payment inputs in M1; focus order follows visual order list → detail content → Add to cart → cart.
- Support system font scaling; truncate long names with ellipsis while keeping price and primary CTA visible without overlap.
- Dark theme tokens maintain AA contrast; disabled controls use disabled color and are excluded from activation semantics.