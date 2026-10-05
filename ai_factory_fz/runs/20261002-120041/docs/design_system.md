# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #0B5FFF | #5B9BFF |
| primary_container | #E8F0FF | #12325F |
| on_primary | #FFFFFF | #001A40 |
| secondary | #1F6B4A | #6FDBA8 |
| secondary_container | #E3F6EC | #0F3A28 |
| background | #F5F7FA | #0E1116 |
| surface | #FFFFFF | #1A1F27 |
| surface_variant | #EEF2F7 | #262C36 |
| on_surface | #12171F | #E8ECF2 |
| on_surface_variant | #5A6575 | #A8B0BD |
| outline | #C5CDD8 | #3E4654 |
| error | #B3261E | #F2B8B5 |
| error_container | #F9DEDC | #8C1D18 |
| success | #1B7A3D | #81C995 |
| warning | #9A6700 | #F5C518 |
| price | #0A3D91 | #8AB4F8 |
| cart_badge | #D93025 | #F28B82 |
| scrim | #00000066 | #00000099 |
| image_placeholder | #D8DEE8 | #2F3642 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| display_small | 28.0 | 700 | 36.0 |
| headline_medium | 22.0 | 600 | 28.0 |
| title_large | 18.0 | 600 | 24.0 |
| title_medium | 16.0 | 600 | 22.0 |
| body_large | 16.0 | 400 | 24.0 |
| body_medium | 14.0 | 400 | 20.0 |
| label_large | 14.0 | 600 | 20.0 |
| label_medium | 12.0 | 500 | 16.0 |
| price_large | 24.0 | 700 | 32.0 |
| price_medium | 16.0 | 700 | 22.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 dp. Corner radii: 0, 4, 8, 12, 16, 24 dp.

## Shared widgets
- **AppTopBar**: Top app bar with screen title, optional back affordance (≥48dp), and CartBadgeButton. Uses surface/on_surface tokens; semantics announce screen name.
- **CartBadgeButton**: Icon button (≥48dp) navigating to /cart; shows item-count badge when CartNotifier total quantity > 0. Semantic label: Cart, N items.
- **SearchField**: Full-width search TextField (≥48dp height) filtering ProductListNotifier by name/brand query. Clear button and semantics label Search laptops.
- **BrandFilterChips**: Horizontal chip row for Dell, Apple, HP, Lenovo (multi-select). Min height 48dp; selected state uses primary_container. Updates brand filter on ProductListNotifier.
- **PriceRangeFilter**: Min/max price filter controls in cents displayed as USD (e.g. $0–$3000). Applies minPriceCents/maxPriceCents to ProductListNotifier; touch targets ≥48dp.
- **ProductCard**: List tile/card: product image or ImagePlaceholder, name (title_medium), brand (label_medium), PriceText from priceCents+USD. Entire card tappable ≥48dp; semantic label includes name and formatted price.
- **PriceText**: Formats integer minor units (cents) + ISO 4217 USD as $X,XXX.XX (e.g. 149999 → $1,499.99). Never uses floating-point money types. Uses price_medium or price_large style and price color token.
- **ImagePlaceholder**: Degraded image fallback when asset missing; surface_variant background with laptop icon and semantic label Product image unavailable.
- **PrimaryButton**: Filled CTA (primary/on_primary), min height 48dp, corner radius 12. Used for Add to cart and Retry. Disabled when out of stock.
- **QuantityStepper**: Minus / quantity / plus controls each ≥48dp. Decrease to 0 removes line. Semantic labels Decrease quantity, Quantity N, Increase quantity.
- **LoadingStateView**: Centered CircularProgressIndicator with optional body_medium message Loading catalog… / Loading product…. Blocks interaction until AsyncValue resolves.
- **EmptyStateView**: Centered message + optional illustration for empty catalog or no search/filter matches. Includes Clear filters action when filters active.
- **ErrorStateView**: Error icon, message, and Retry PrimaryButton (≥48dp). Used when LocalCatalogDataSource fails or product id missing.
- **CartLineItem**: Cart row: name, PriceText unit snapshot (cents+USD), QuantityStepper, line subtotal. Remove when quantity reaches 0. Semantics include name and quantity.
- **CartSummaryBar**: Bottom bar showing item count and PriceText cart total from in-memory CartState. Demo-only; no checkout CTA in M1.

## Screens
### SCR-01 ProductListScreen (`/products`)
Browse the seeded local mock laptop catalog (12–15 SKUs across Dell, Apple, HP, Lenovo) with client-side search and brand/price-range filters; show name and USD price from integer cents; entry point for the demo.
- Components: AppTopBar, CartBadgeButton, SearchField, BrandFilterChips, PriceRangeFilter, ProductCard, PriceText, ImagePlaceholder, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading, empty, empty_filtered, error, success
- Stories: US-001, US-003

### SCR-02 ProductDetailScreen (`/products/:id`)
Show a single laptop’s name, brand, unit price (cents+USD), short description/specs summary, and image or placeholder; allow add-to-cart for in-stock demo SKUs; back returns to list with browse context preserved. Flagship New DELL XPS 13 9300 Laptop must show $1,499.99 from 149999 cents USD.
- Components: AppTopBar, CartBadgeButton, PriceText, ImagePlaceholder, PrimaryButton, LoadingStateView, ErrorStateView
- States: loading, error, success, out_of_stock
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Manage the session-only in-memory cart: line items with name, unit price snapshot (cents+USD), quantity steppers (≥48dp), remove at quantity 0; totals update immediately with no backend. Cart may be empty after process restart.
- Components: AppTopBar, CartLineItem, QuantityStepper, PriceText, CartSummaryBar, EmptyStateView, ImagePlaceholder
- States: empty, success
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductCard for a laptop SKU → go_router push /products/:id
- SCR-02 → SCR-01: Back / AppTopBar leading → pop; ProductListNotifier browse query/filters preserved
- SCR-01 → SCR-03: Tap CartBadgeButton → go_router push /cart
- SCR-02 → SCR-03: Tap CartBadgeButton or after Add to cart success affordance → push /cart
- SCR-03 → SCR-01: Back from cart or Continue browsing empty-state action → pop/go /products
- SCR-03 → SCR-02: Optional tap on CartLineItem name → push /products/:id for that line’s productId

## Accessibility
- Minimum touch target 48×48dp for ProductCard, SearchField clear, BrandFilterChips, PriceRangeFilter controls, PrimaryButton, QuantityStepper buttons, CartBadgeButton, Retry, and Back.
- Text contrast ≥ WCAG AA: on_surface on background/surface and on_primary on primary in light and dark themes.
- All images and icons provide Semantics/semanticLabel (product name image, Cart, Search laptops, Increase/Decrease quantity, Retry, Back).
- PriceText announces formatted currency for screen readers (e.g. 1499 dollars and 99 cents) from integer cents + USD.
- ProductCard semantics combine name, brand, and price; exclude decorative placeholders from focus when ImagePlaceholder is used.
- LoadingStateView and ErrorStateView announce status via Semantics liveRegion / AnnounceSemanticsEvents.
- Empty filtered results: EmptyStateView with Clear filters action labeled and focusable.
- Focus order: AppTopBar → search/filters → product list/detail content → primary CTA / cart summary; no horizontal scroll of primary content on phone viewports.
- Cart badge badge count included in CartBadgeButton semantic label (Cart, N items).
- Do not rely on color alone for error/out-of-stock; pair with text labels.