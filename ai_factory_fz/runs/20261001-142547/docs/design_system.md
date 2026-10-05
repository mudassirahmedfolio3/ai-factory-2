# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| brandPrimary | #0B6E4F | #3DDC97 |
| brandPrimaryVariant | #085A41 | #2BB87A |
| brandSecondary | #1B4965 | #7EB8D8 |
| background | #F7FAF8 | #0F1412 |
| surface | #FFFFFF | #1A211E |
| surfaceVariant | #E8F0EC | #24302B |
| onBackground | #122018 | #E8F0EC |
| onSurface | #122018 | #E8F0EC |
| onPrimary | #FFFFFF | #0A1F16 |
| textPrimary | #122018 | #E8F0EC |
| textSecondary | #4A5C54 | #A8B8B0 |
| textDisabled | #8A9A92 | #6A7A72 |
| price | #0B6E4F | #3DDC97 |
| ratingStar | #E6A817 | #F0C040 |
| ratingStarEmpty | #C5D0CA | #3A4540 |
| divider | #D4E0DA | #2E3A35 |
| error | #C62828 | #EF9A9A |
| onError | #FFFFFF | #1A0000 |
| success | #2E7D32 | #81C784 |
| imagePlaceholder | #DCE8E2 | #2A3530 |
| cartBadge | #C62828 | #EF5350 |
| appBar | #0B6E4F | #1A211E |
| onAppBar | #FFFFFF | #E8F0EC |
| outline | #A8B8B0 | #4A5C54 |
| scrim | #80000000 | #CC000000 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| displayLarge | 32.0 | 700 | 40.0 |
| headlineMedium | 24.0 | 700 | 32.0 |
| titleLarge | 20.0 | 600 | 28.0 |
| titleMedium | 16.0 | 600 | 24.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| labelLarge | 14.0 | 600 | 20.0 |
| labelMedium | 12.0 | 500 | 16.0 |
| priceLarge | 28.0 | 700 | 36.0 |
| priceMedium | 16.0 | 700 | 24.0 |
| caption | 12.0 | 400 | 16.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 dp. Corner radii: 0, 4, 8, 12, 16, 24 dp.

## Shared widgets
- **PulseAppBar**: Branded AppBar showing PulsePhones wordmark/title, optional cart IconButton with quantity badge (min 48dp touch target), semantic label PulsePhones storefront. Uses brandPrimary/appBar tokens; back chevron on detail/cart.
- **ProductListTile**: List row for a smartphone: 72dp image/placeholder, product name (titleMedium), USD price from integer cents via PriceText (priceMedium), StarRatingSummary. Min height 72dp; entire tile Semantics button with label including name, price, and rating. Tap navigates to /products/:id.
- **ProductImagePlaceholder**: Aspect-ratio box (1:1 list, 4:3 detail) with imagePlaceholder fill, optional phone silhouette Icon, Semantics image label Product image for {name} or Placeholder image for {name}.
- **PriceText**: Formats integer USD minor units (cents) plus ISO 4217 USD to locale display e.g. $899.99 for 89999. Never accepts float storage; uses price color token and priceMedium/priceLarge styles.
- **StarRatingSummary**: Row of 5 stars (filled/half/empty via ratingStar tokens) plus numeric average (e.g. 4.5) in labelMedium/textSecondary. Semantics label Rated {n} out of 5 stars. Touch targets not required when display-only.
- **PrimaryButton**: Filled button min height 48dp, brandPrimary fill, onPrimary label (labelLarge). Used for Add to cart. Semantics button with explicit action label.
- **QuantityStepper**: Row of decrease IconButton, quantity Text (titleMedium), increase IconButton; each control min 48dp. Decrease at qty 1 becomes remove or disables per cart rules. Semantics labels Decrease quantity, Increase quantity, Quantity {n}.
- **AsyncStateView**: Reusable loading (CircularProgressIndicator + Loading catalog), empty (illustration + message + optional retry), error (error color message + Retry PrimaryButton). Used by list/detail/cart AsyncValue branches.
- **CartLineItem**: Cart row: product name, PriceText unit snapshot (cents+USD), QuantityStepper, remove IconButton (48dp). Semantics summarize name, unit price, quantity.
- **SectionHeader**: titleLarge section title for Key details on detail screen; textPrimary; padding from spacing scale.

## Screens
### SCR-01 ProductListScreen (`/products`)
PulsePhones-branded scrollable browse of 12–20 seeded smartphones showing name, USD price from integer cents, star rating summary, and image/placeholder so shoppers can compare models and open a product. Initial route and demo home; no network or auth.
- Components: PulseAppBar, ProductListTile, ProductImagePlaceholder, PriceText, StarRatingSummary, AsyncStateView
- States: loading, empty, error, success
- Stories: US-001, US-002

### SCR-02 ProductDetailScreen (`/products/:id`)
Shows one seeded smartphone: name, USD price from integer cents (e.g. $899.99 for 89999), key details/specs, star rating, image/placeholder; optional Add to cart for in-memory cart. Back returns to list without losing local catalog state.
- Components: PulseAppBar, ProductImagePlaceholder, PriceText, StarRatingSummary, SectionHeader, PrimaryButton, AsyncStateView
- States: loading, empty, error, success
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Optional M1 in-memory cart: line items with product name, unit price snapshot (cents + USD), quantity increase/decrease/remove. Session-only; empty after process kill. No persistence, auth, or payments.
- Components: PulseAppBar, CartLineItem, PriceText, QuantityStepper, AsyncStateView, PrimaryButton
- States: empty, success
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductListTile for product id → go_router push /products/:id
- SCR-02 → SCR-01: AppBar back / system back → pop to /products; CatalogRepository state retained
- SCR-02 → SCR-03: After Add to cart (or AppBar cart icon) → go /cart showing new line qty 1
- SCR-01 → SCR-03: AppBar cart IconButton when badge > 0 → go /cart
- SCR-03 → SCR-01: AppBar back / Continue browsing → pop or go /products
- SCR-03 → SCR-02: Optional tap CartLineItem name → push /products/:id for that product

## Accessibility
- Minimum touch target 48dp for ProductListTile actions, AppBar icons, PrimaryButton, QuantityStepper, Retry, Remove.
- WCAG AA contrast: textPrimary on background/surface ≥ 4.5:1; onPrimary on brandPrimary ≥ 4.5:1; price and body text meet AA in light and dark.
- Semantics labels on all images/icons: product images, star icons, cart badge, back, add/remove/stepper.
- ProductListTile Semantics button: {name}, {formatted price}, rated {n} out of 5.
- PrimaryButton Semantics: Add {name} to cart.
- Announce AsyncStateView loading/empty/error via Semantics liveRegion or AnnounceSemantics where practical.
- Do not rely on color alone for rating or error; pair with text/icons.
- Support system text scaling; avoid clipping primary prices and titles at 1.3x scale.
- Focus order: AppBar → list/content → primary CTA (Add to cart / Retry).
- English USD-only M1 copy; prices always formatted from integer cents, never spoken as raw float storage values.