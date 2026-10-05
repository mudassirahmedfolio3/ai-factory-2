# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #0B6E4F | #3DDBA5 |
| on_primary | #FFFFFF | #003828 |
| primary_container | #D0F5E6 | #08553C |
| on_primary_container | #002117 | #D0F5E6 |
| secondary | #2C5F7C | #8EC8E8 |
| on_secondary | #FFFFFF | #00344A |
| background | #F7F9F8 | #101413 |
| on_background | #1A1F1D | #E2E8E5 |
| surface | #FFFFFF | #1A1F1D |
| on_surface | #1A1F1D | #E2E8E5 |
| surface_variant | #E8EEEB | #2A302D |
| on_surface_variant | #3F4944 | #BFC9C3 |
| outline | #6F7974 | #89938D |
| error | #B3261E | #F2B8B5 |
| on_error | #FFFFFF | #601410 |
| success | #1B7A3E | #6FDB8C |
| on_success | #FFFFFF | #003916 |
| warning | #9A6700 | #F5C84C |
| on_warning | #FFFFFF | #3D2800 |
| out_of_stock | #8A3B32 | #E8A39A |
| price | #0B6E4F | #3DDBA5 |
| scrim | #00000099 | #000000B3 |
| cart_badge | #B3261E | #F2B8B5 |
| on_cart_badge | #FFFFFF | #601410 |
| image_placeholder | #D5DDD8 | #3A413D |
| divider | #D5DDD8 | #3A413D |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| display_large | 32.0 | 700 | 40.0 |
| headline_medium | 24.0 | 600 | 32.0 |
| title_large | 20.0 | 600 | 28.0 |
| title_medium | 16.0 | 600 | 24.0 |
| body_large | 16.0 | 400 | 24.0 |
| body_medium | 14.0 | 400 | 20.0 |
| label_large | 14.0 | 600 | 20.0 |
| label_medium | 12.0 | 500 | 16.0 |
| price_large | 22.0 | 700 | 28.0 |
| price_medium | 16.0 | 700 | 24.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 dp. Corner radii: 0, 4, 8, 12, 16, 24 dp.

## Shared widgets
- **AppTopBar**: App bar with title, optional back affordance (48dp), and CartBadgeButton. Uses surface/on_surface tokens. Preserves list filter/search in ProductListNotifier when navigating back from detail.
- **CartBadgeButton**: Icon button (min 48×48dp) showing shopping cart with numeric badge from CartNotifier item count. Semantic label includes count, e.g. Cart, 3 items. Navigates to /cart.
- **ProductCard**: Catalog list tile: product image or ImagePlaceholder (semantic label = product name), name (title_medium), tax-inclusive price from integer minor units + ISO 4217 via PriceText, OutOfStockChip when stock <= 0. Entire card is one 48dp-min tap target navigating to /products/:id.
- **PriceText**: Formats integer minor units (cents) with currency code (e.g. USD) as tax-inclusive display string. Never uses floating-point money. Uses price/price_large or price_medium tokens.
- **OutOfStockChip**: Compact availability chip using out_of_stock/on_surface colors; text Out of stock; exposed to screen readers as product unavailable.
- **CategoryFilterBar**: Horizontal chip row for Apparel, Accessories, Home, Essentials (plus All). Selected chip uses primary_container. Each chip min height 48dp. Updates ProductListNotifier.categorySlug.
- **SearchField**: Text field filtering product names; clear button restores full list. Hint Search products; semantics announce result count changes. Min touch target 48dp for clear icon.
- **ImagePlaceholder**: Surface-variant block with product icon when image URL missing/fails; always paired with semantic label describing the product.
- **PrimaryButton**: Filled CTA using primary/on_primary; min height 48dp; disabled state for out-of-stock or stock-limit (reduced opacity, not focusable as enabled). Used for Add to cart.
- **QuantityStepper**: Minus / quantity label / plus controls; each control ≥48dp. Quantity never below 1 unless line removed; plus disabled at mock stock limit with clear semantics.
- **EmptyStateView**: Centered illustration/icon, title, body message, optional retry for empty catalog or empty cart. Uses body_large and on_surface_variant.
- **ErrorStateView**: Error icon, message, Retry button (48dp) that reloads LocalCatalogDataSource / notifier. Meets WCAG AA contrast on background.
- **LoadingStateView**: Centered CircularProgressIndicator with semantic label Loading products or Loading product details; blocks interaction until AsyncValue resolves.
- **CartLineItem**: Cart row: name, PriceText unit snapshot (cents + currency), QuantityStepper, remove (48dp). Reflects CartNotifier; remove deletes line.
- **StockAvailabilityLabel**: Shows In stock (N available) or Out of stock using success/out_of_stock colors; used on detail for default variant.

## Screens
### SCR-01 ProductListScreen (`/products`)
Browse mock catalog with product cards (name, tax-inclusive price from cents + USD, image/placeholder, out-of-stock), category filter, name search, and cart badge. Initial route for M1; serves discovery without auth or backend.
- Components: AppTopBar, CartBadgeButton, SearchField, CategoryFilterBar, ProductCard, PriceText, OutOfStockChip, ImagePlaceholder, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading, empty, error, success
- Stories: US-001, US-002, US-003

### SCR-02 ProductDetailScreen (`/products/:id`)
Show single product name, tax-inclusive price (cents + currency), image, description, category, and stock for default variant; Add to cart for in-stock items; back returns to list with filter/search preserved.
- Components: AppTopBar, CartBadgeButton, ImagePlaceholder, PriceText, StockAvailabilityLabel, OutOfStockChip, PrimaryButton, QuantityStepper, LoadingStateView, ErrorStateView
- States: loading, error, success, out_of_stock
- Stories: US-002, US-003

### SCR-03 CartScreen (`/cart`)
Session-only in-memory cart: line items with name, unit price snapshot (cents + currency), quantity controls, remove; enforce min qty 1 unless removed and max qty = mock stock; empty on process restart.
- Components: AppTopBar, CartLineItem, PriceText, QuantityStepper, EmptyStateView, PrimaryButton
- States: empty, success
- Stories: US-003

## Navigation
- SCR-01 → SCR-02: Tap ProductCard with product id → go_router push /products/:id
- SCR-02 → SCR-01: Back / AppTopBar leading → pop; ProductListNotifier keeps categorySlug and search query
- SCR-01 → SCR-03: Tap CartBadgeButton → go_router push /cart
- SCR-02 → SCR-03: Tap CartBadgeButton → go_router push /cart
- SCR-03 → SCR-01: Back from cart or Continue shopping when empty → pop or go /products
- SCR-02 → SCR-03: Successful Add to cart (optional snackbar action View cart) → push /cart

## Accessibility
- Minimum touch target 48×48dp for all interactive controls (cards, chips, icons, steppers, buttons, clear search).
- Text and icon contrast meet WCAG AA: on_background/on_surface on background/surface ≥ 4.5:1; primary on on_primary and error/on_error pairs verified for light and dark.
- All product images and ImagePlaceholders expose Semantics label with product name; decorative icons excludeSemantics or labeled.
- CartBadgeButton announces Cart, N items; OutOfStockChip and StockAvailabilityLabel announce availability to TalkBack.
- PrimaryButton Add to cart disabled when out of stock or at stock limit; Semantics hint explains why (Out of stock or Maximum stock reached).
- LoadingStateView uses live region / Semantics label so screen readers hear Loading… then content.
- EmptyStateView and ErrorStateView provide readable titles/body; Retry is focusable and labeled Retry loading products.
- QuantityStepper minus/plus have labels Decrease quantity and Increase quantity; quantity value is a Semantics value.
- Focus order: search → category chips → product list → cart badge; on detail: back → cart → image → content → quantity → add.
- Do not rely on color alone for out-of-stock: chip text plus optional strike or badge pattern.
- Support system text scaling; price and titles reflow without clipping on common phone widths (≥320dp).
- No personal data, passwords, or payment fields in M1; nothing to announce as secure entry.