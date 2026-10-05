# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1B3A4B | #7EB8D4 |
| onPrimary | #FFFFFF | #0A1A22 |
| secondary | #A84A1A | #E8956A |
| onSecondary | #FFFFFF | #2A1208 |
| background | #F7F5F2 | #121418 |
| onBackground | #1A1C1E | #E8EAED |
| surface | #FFFFFF | #1E2126 |
| onSurface | #1A1C1E | #E8EAED |
| surfaceVariant | #EDE9E3 | #2A2E35 |
| onSurfaceVariant | #5A5F66 | #B0B5BC |
| outline | #C5C0B8 | #4A5058 |
| error | #B3261E | #F2B8B5 |
| onError | #FFFFFF | #601410 |
| success | #1B6B3A | #81C995 |
| price | #0F5C2E | #8FD4A8 |
| disabled | #9E9A94 | #6B7078 |
| scrim | #99000000 | #99000000 |
| cartBadge | #A84A1A | #E8956A |
| imagePlaceholder | #E0DBD4 | #333840 |

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
| labelMedium | 12.0 | 500 | 16.0 |
| priceLarge | 22.0 | 700 | 28.0 |
| priceMedium | 16.0 | 700 | 24.0 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 4, 8, 12, 16, 24 dp.

## Shared widgets
- **SsAppBar**: Top app bar with ShirtStack title or screen title, optional back affordance (48dp), and cart icon button with optional badge count. Uses primary/onPrimary tokens; semantic labels on all actions.
- **ProductCard**: Catalog card showing primary image (semantic label = product title), title (titleMedium), formatted USD price from integer cents (priceMedium), and attribute chips for available sizes, color, and fit type. Minimum tap target 48dp; used in ProductListScreen grid/list.
- **FilterChipBar**: Horizontal scrollable filter chips for size, color, price range, and shirt type. Selected state uses primary fill; unselected uses surfaceVariant. Each chip ≥48dp height; announces selection state to screen readers.
- **SearchField**: Real-time client-side search TextField filtering by product title and attributes. Clear button (≥48dp); hint and semantics label 'Search shirts'.
- **VariantSelector**: Single-select size and color chip groups on product detail. Selected variant highlighted with primary outline/fill; disabled unavailable options use disabled token. Each option ≥48dp touch target.
- **StickyAddToCartBar**: Pinned bottom bar on ProductDetailScreen with quantity stepper and Add to cart primary button. Bar and button height ≥48dp; remains visible while scrolling. Shows brief SnackBar confirmation on success.
- **PriceText**: Formats integer cents + ISO 4217 USD as display string (e.g. $27.99). Uses price color token; never floating-point math. Semantics: 'Price {formatted}'.
- **EmptyState**: Centered illustration placeholder, title, and body for empty catalog or no filter/search matches. Optional clear-filters action button ≥48dp.
- **ErrorState**: Error icon, message, and Retry button (≥48dp) for catalog load failures. Uses error/onError tokens.
- **LoadingSkeleton**: Shimmer placeholders matching ProductCard or detail layout while AsyncNotifier is loading. Announce 'Loading' via semantics live region.
- **CartLineItem**: Cart row with product name, unit price (cents copied at add), size/color, quantity stepper (−/+, ≥48dp), and remove control. Decrement to zero or remove deletes the line and recalculates subtotal.
- **ReturnsPolicySection**: Expandable or static section on product detail: 30-day returns on unworn items with original tags; refunds to original payment method; exchanges as return plus new order; contact email to initiate return.
- **SsPrimaryButton**: Filled primary CTA, min height 48dp, min width 48dp, labelLarge on onPrimary. Disabled state uses disabled token; always has semantic label.
- **SsIconButton**: Icon-only control with 48dp minimum tap target and required semanticLabel (e.g. Open cart, Go back, Decrease quantity).

## Screens
### SCR-01 ProductListScreen (`/products`)
Browse the locally seeded men's shirts catalog (~20–40 SKUs) with title, formatted USD price, primary image, sizes, color, and fit type; support client-side filters (size, color, price range, shirt type) and real-time search; entry point for M1 demo.
- Components: SsAppBar, SearchField, FilterChipBar, ProductCard, PriceText, LoadingSkeleton, EmptyState, ErrorState, SsIconButton
- States: loading, empty, error, success
- Stories: US-001

### SCR-02 ProductDetailScreen (`/products/:id`)
Show shirt title, description, formatted USD price, primary image, size/color selectors, fit type, and 30-day returns policy; sticky add-to-cart bar (≥48dp) adds selected variant quantity 1 to in-memory cart with SnackBar confirmation.
- Components: SsAppBar, PriceText, VariantSelector, StickyAddToCartBar, ReturnsPolicySection, SsPrimaryButton, LoadingSkeleton, EmptyState, ErrorState, SsIconButton
- States: loading, empty, error, success
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Display in-memory cart line items with product name, unit price (cents at add), size/color, quantity controls, and running USD subtotal; remove or decrement to zero removes line; cart clears on app restart in M1.
- Components: SsAppBar, CartLineItem, PriceText, EmptyState, SsPrimaryButton, SsIconButton
- States: empty, success
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductCard for a shirt SKU
- SCR-02 → SCR-01: Tap back in SsAppBar
- SCR-01 → SCR-03: Tap cart icon in SsAppBar
- SCR-02 → SCR-03: Tap cart icon in SsAppBar or after add-to-cart confirmation action
- SCR-03 → SCR-01: Tap back or Continue shopping when cart empty
- SCR-03 → SCR-02: Tap a cart line item to reopen that product detail

## Accessibility
- Minimum touch target 48×48 dp for all interactive controls (chips, buttons, icon buttons, quantity steppers, ProductCard).
- Text and icon contrast meets WCAG 2.1 AA against light and dark theme backgrounds (onSurface on background/surface; onPrimary on primary; onSecondary on secondary; price on surface).
- All images and icons expose semantic labels (product title for primary images; action verbs for icons).
- Support system font scaling (textScaleFactor) without clipping on ProductListScreen and ProductDetailScreen; wrap long titles with maxLines and ellipsis where needed.
- Announce loading via semantics live region; EmptyState and ErrorState expose clear headings and actionable Retry/Clear filters labels.
- VariantSelector announces selected size and color to screen readers; StickyAddToCartBar button label includes selected variant when present (e.g. Add Medium Blue to cart).
- Focus order follows visual reading order: search/filters → list → app bar actions; detail: image → info → variants → returns → sticky CTA.
- Do not rely on color alone for selected filter/variant state; use outline weight or checkmark plus color.
- Cart badge count is also available via Semantics on the cart icon (e.g. Cart, 3 items).
- Respect reduced-motion preferences: disable shimmer animation when system reduce-motion is on; keep static skeleton.