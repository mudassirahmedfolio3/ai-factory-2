# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #7A9E8E | #9BB8AA |
| primary_variant | #5F8273 | #B5CDBF |
| background | #F7F3EB | #1C1F1D |
| surface | #FFFCF7 | #2A2E2B |
| surface_variant | #EFE9DF | #353A37 |
| text_primary | #2C2C2C | #F2EDE4 |
| text_secondary | #5A5A5A | #C4BEB4 |
| text_on_primary | #FFFFFF | #1C1F1D |
| border | #D9D2C6 | #4A504C |
| error | #B3261E | #F2B8B5 |
| success | #4A7C59 | #8FBC9A |
| disabled | #B8B2A8 | #6B716D |
| scrim | #00000066 | #00000099 |
| image_placeholder | #E4DED3 | #3F4541 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| display | 28.0 | 600 | 36.0 |
| headline | 22.0 | 600 | 28.0 |
| title | 18.0 | 600 | 24.0 |
| body | 16.0 | 400 | 24.0 |
| body_emphasis | 16.0 | 600 | 24.0 |
| label | 14.0 | 500 | 20.0 |
| caption | 12.0 | 400 | 16.0 |
| price | 20.0 | 600 | 28.0 |
| button | 16.0 | 600 | 24.0 |

Spacing scale: 4, 8, 12, 16, 24, 32, 48 dp. Corner radii: 8, 12, 16, 24 dp.

## Shared widgets
- **SoftAuraAppBar**: Top app bar with SoftAura brand title or screen title, charcoal text on warm ivory (dark: light text on surface), optional trailing cart icon button with ≥48dp hit area and semantic label Cart.
- **ProductCard**: Browse list card showing rounded product image (radius 16), product name (title), formatted USD price from integer cents (e.g. 1299 → $12.99), and category chip (Body Wash | Cleansers | Moisturizers | Face Care). Entire card tappable ≥48dp tall; sage accent on chip/border; Semantics label includes name, category, and price.
- **ProductImage**: Rounded product imagery (corner radius 16–24) with warm ivory/surface_variant placeholder, BoxFit.cover, and required semanticLabel describing the product.
- **PriceText**: Displays money from integer minor units (cents) + ISO 4217 USD as $X.XX without floating-point arithmetic; uses price type style and charcoal/primary contrast.
- **CategoryChip**: Compact label for one of Body Wash, Cleansers, Moisturizers, Face Care; sage primary fill or outline on ivory; min height 32 with parent ensuring 48dp touch if interactive.
- **PrimaryButton**: Filled sage (#7A9E8E) button with text_on_primary label, min height/width 48dp, used for Add to cart and Retry actions.
- **LoadingStateView**: Centered CircularProgressIndicator using primary accent with optional caption Loading SoftAura products; used while AsyncValue is loading.
- **EmptyStateView**: Centered illustration/placeholder, headline and body copy when catalog or cart has zero items, optional PrimaryButton CTA.
- **ErrorStateView**: Error message with Retry PrimaryButton (≥48dp); shown when catalog load fails; charcoal text on ivory, error color for icon.
- **CartLineItem**: Cart row with product name and unit price snapshot (cents + USD copied at add time); 48dp min row height; Semantics for name and price.

## Screens
### SCR-01 ProductListScreen (`/products`)
Scrollable SoftAura Skin Care browse screen showing all 24 seeded mock SKUs as product cards with name, USD price from integer cents, rounded imagery, and category membership on warm ivory with sage accent and charcoal text.
- Components: SoftAuraAppBar, ProductCard, ProductImage, PriceText, CategoryChip, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading, empty, error, success
- Stories: US-001, US-002

### SCR-02 ProductDetailScreen (`/products/:id`)
Product detail for a single catalog SKU: name, brand, category, unit price (cents → $X.XX USD), description, and rounded product image with SoftAura styling; optional Add to cart (≥48dp); Android back returns to list with catalog still visible.
- Components: SoftAuraAppBar, ProductImage, PriceText, CategoryChip, PrimaryButton, LoadingStateView, ErrorStateView
- States: loading, error, success
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Optional M1 in-memory session cart listing line items with product name and unit price snapshot (cents + USD) copied at add time; contents survive list/detail navigation within the same process and clear on process kill; no auth, payment, or persistence.
- Components: SoftAuraAppBar, CartLineItem, PriceText, EmptyStateView, PrimaryButton
- States: empty, success
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductCard → go_router push /products/:id
- SCR-02 → SCR-01: Android system back or AppBar back → pop to /products with catalog state retained
- SCR-01 → SCR-03: Tap AppBar cart icon → go_router push /cart
- SCR-02 → SCR-03: Tap AppBar cart icon or after Add to cart feedback → go_router push /cart
- SCR-03 → SCR-01: Android system back or AppBar back → pop; cart Notifier state remains for session

## Accessibility
- All interactive controls meet minimum 48×48 dp touch targets (ProductCard, PrimaryButton, AppBar back/cart icons, Retry).
- Charcoal text (#2C2C2C) on warm ivory (#F7F3EB) and light text (#F2EDE4) on dark surface (#2A2E2B) meet WCAG AA contrast (≥4.5:1 for body text).
- Sage primary (#7A9E8E) on white/ivory button label uses text_on_primary (#FFFFFF) meeting AA for large/button text.
- Every ProductImage and icon includes a non-empty Semantics / semanticLabel (product name or action, e.g. Add to cart, Go back, Open cart).
- PriceText announces formatted currency (e.g. 12 dollars 99 cents) via Semantics, never raw cents alone.
- ProductCard Semantics merges name, category, and price into one focusable announcement.
- Navigation supports standard Android back behavior from detail and cart to prior screen without trapping focus.
- Loading, empty, and error states expose liveRegion / Semantics announcements so screen readers hear status changes.
- CategoryChip text remains readable at 14sp with sufficient contrast against sage outline or soft sage fill.
- Do not rely on color alone: category chips include text labels; error state includes icon plus Retry label.