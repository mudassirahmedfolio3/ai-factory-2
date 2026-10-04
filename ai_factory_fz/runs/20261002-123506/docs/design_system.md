# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #8B5E3C | #D4A574 |
| primary_container | #F5E6D8 | #3D2A1C |
| on_primary | #FFFFFF | #1A120C |
| secondary | #6B7C6E | #A8B8AB |
| secondary_container | #E4EBE5 | #2A332C |
| background | #FAF8F5 | #141210 |
| surface | #FFFFFF | #1E1B18 |
| surface_variant | #F0ECE6 | #2A2622 |
| on_background | #1C1917 | #F5F0EB |
| on_surface | #1C1917 | #F5F0EB |
| on_surface_variant | #5C5650 | #B8B0A6 |
| outline | #C9C2B8 | #4A453F |
| error | #B3261E | #F2B8B5 |
| on_error | #FFFFFF | #601410 |
| error_container | #F9DEDC | #8C1D18 |
| success | #2E7D4F | #81C995 |
| warning | #B86E00 | #F5C26B |
| star_filled | #C9A227 | #E8C547 |
| star_empty | #D6D0C8 | #4A453F |
| price | #5A3E2B | #E8C9A8 |
| badge | #8B5E3C | #D4A574 |
| scrim | #00000099 | #000000CC |
| disabled | #9E968C | #6B645C |
| divider | #E8E2DA | #332E29 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| display_large | 32.0 | 600 | 40.0 |
| headline_large | 24.0 | 600 | 32.0 |
| headline_medium | 20.0 | 600 | 28.0 |
| title_large | 18.0 | 600 | 24.0 |
| title_medium | 16.0 | 600 | 22.0 |
| title_small | 14.0 | 600 | 20.0 |
| body_large | 16.0 | 400 | 24.0 |
| body_medium | 14.0 | 400 | 20.0 |
| body_small | 12.0 | 400 | 16.0 |
| label_large | 14.0 | 600 | 20.0 |
| label_medium | 12.0 | 600 | 16.0 |
| label_small | 11.0 | 500 | 14.0 |
| price_large | 22.0 | 700 | 28.0 |
| price_medium | 16.0 | 700 | 22.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 dp. Corner radii: 0, 4, 8, 12, 16, 24 dp.

## Shared widgets
- **AppTopBar**: Material app bar with title, optional leading back (≥48dp), and trailing actions (e.g. cart icon with badge count). Uses surface/on_surface tokens; title uses title_large.
- **ProductCard**: Tappable catalog card (≥48dp hit area) showing primary image or ImagePlaceholder, product name (title_small, max 2 lines), formatted price via PriceText, and optional category chip. Semantics: product name + price as button label.
- **PriceText**: Formats integer minor units (cents) + ISO 4217 currency to display string without floats (e.g. 1999 USD → $19.99). Uses price color token and price_medium/price_large style.
- **SearchField**: Full-width text field for case-insensitive catalog search. Clear affordance (≥48dp) restores prior filter-only results. Hint and semantics: Search jewellery.
- **FilterChipBar**: Horizontal scroll of filter chips for category (earrings|necklaces|bracelets|rings), metal (gold-tone|silver-tone|rose-gold), occasion (everyday|work|gift|party), and price-range entry. Chips ≥48dp tall; selected state uses primary_container.
- **PriceRangeFilter**: Sheet or dialog to set minPriceCents and maxPriceCents as integers. Apply/Clear actions ≥48dp. Display bounds via PriceText.
- **StarRating**: Read-only 1–5 star display using star_filled/star_empty tokens. Aggregate average on detail header; per-review stars in ReviewTile. Semantic label includes numeric rating.
- **ReviewTile**: List row for one mock review: StarRating + review body (body_medium). Used in ProductDetailScreen review list.
- **PrimaryButton**: Filled CTA (e.g. Add to cart) min height 48dp, full-width on mobile. Disabled when out of stock using disabled token. Semantics match visible label.
- **QuantityStepper**: Minus / quantity / plus controls, each touch target ≥48dp. Decrease to 0 removes cart line. Never allows quantity below 0. Semantics: Decrease quantity, Increase quantity, Quantity N.
- **CartLineItem**: Cart row: product name, unit PriceText snapshot (cents+currency at add time), QuantityStepper, line total (qty × unitPriceCents integer math).
- **CartBadge**: Overlay badge on cart icon showing sum of line quantities; hidden when cart empty. Contrast WCAG AA on badge/on_primary.
- **ImagePlaceholder**: Neutral surface_variant block with jewellery icon when asset missing. Requires semanticLabel (product name or Jewellery image placeholder).
- **EmptyState**: Centered illustration/icon + title (title_medium) + body (body_medium) + optional clear-filters action. Used for zero search/filter results, empty reviews, empty cart.
- **ErrorState**: Error message with Retry button (≥48dp). Shown when mock catalog load fails or product id not found.
- **LoadingState**: Centered CircularProgressIndicator with optional label Loading jewellery… Semantics: busy.
- **StockBadge**: Chip showing In stock (success) or Out of stock (error/on_surface_variant). Controls Add to cart enabled state.
- **MetaChip**: Read-only chip for category, metal, or occasion labels on detail and optionally on cards.
- **CartSummaryBar**: Bottom sticky bar on cart with item count and cart total PriceText (sum of line totals in cents). Min height 48dp content area.

## Screens
### SCR-01 ProductListScreen (`/products`)
Browse the seeded local mock Womens Jewellery catalog (~12–20 SKUs including Tropical Earring at 1999 USD cents). Supports case-insensitive search on name/searchable text and AND filters for price range (min/max cents), category, metal, and occasion. Preserves search/filter state when returning from detail. Initial route of the M1 demo.
- Components: AppTopBar, CartBadge, SearchField, FilterChipBar, PriceRangeFilter, ProductCard, PriceText, ImagePlaceholder, LoadingState, EmptyState, ErrorState
- States: loading, success, empty, error
- Stories: US-001, US-002

### SCR-02 ProductDetailScreen (`/products/:id`)
Show a single mock product: name, description, price (cents + USD via PriceText), category, metal, occasion, stock/availability, aggregate star rating (1–5), and mock review list (or empty reviews). Add to cart (≥48dp) for in-stock items increments in-memory cart quantity. System/in-app back returns to list with search/filter preserved.
- Components: AppTopBar, CartBadge, ImagePlaceholder, PriceText, StarRating, ReviewTile, MetaChip, StockBadge, PrimaryButton, LoadingState, EmptyState, ErrorState
- States: loading, success, empty_reviews, error, out_of_stock
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Session-only in-memory cart: line items with name, unit price snapshot (cents + currency), QuantityStepper (≥48dp); decrease to 0 removes line; line and cart totals use integer minor-unit math only. Empty on cold start; no persistence, auth, or checkout in M1.
- Components: AppTopBar, CartLineItem, QuantityStepper, PriceText, CartSummaryBar, EmptyState, LoadingState, ErrorState
- States: loading, success, empty, error
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductCard for a listed SKU (e.g. Tropical Earring) → go_router push /products/:id
- SCR-02 → SCR-01: System back or AppTopBar back → pop; ProductListNotifier retains q and filter state for the session
- SCR-01 → SCR-03: Tap cart action with CartBadge in AppTopBar → go_router push /cart
- SCR-02 → SCR-03: Tap cart action in AppTopBar, or after Add to cart optionally open cart → push /cart
- SCR-03 → SCR-01: System/AppTopBar back from cart → pop to previous (typically ProductListScreen); continue shopping empty-state CTA → go /products
- SCR-03 → SCR-02: Optional tap on CartLineItem name → push /products/:id for that product id

## Accessibility
- Minimum interactive touch target 48×48 dp for Add to cart, filter chips, search clear, cart icon, quantity steppers, Retry, and Clear filters
- Text and icon contrast meet WCAG AA: on_background/on_surface vs background/surface ≥4.5:1 for body; large text ≥3:1; primary CTA on_primary vs primary ≥4.5:1
- All images and icons expose semantic labels (product name for catalog/detail imagery; Cart, Search, Clear search, Back, Decrease quantity, Increase quantity)
- ProductCard announces as button with name and formatted price; StarRating announces average or review rating numerically (e.g. 4.5 out of 5 stars)
- LoadingState sets Semantics busy; ErrorState and EmptyState expose readable titles and actionable Retry/Clear labels
- QuantityStepper never allows values below 0; removing a line announces item removed where platform semantics allow
- Focus order: search → filters → product grid → cart; on detail: image → meta → reviews → Add to cart; support screen readers and TalkBack/VoiceOver
- Do not rely on color alone for stock or filter selection: StockBadge and selected chips include text labels
- PriceText uses locale-aware currency formatting from integer cents only—no float money math affecting announced values