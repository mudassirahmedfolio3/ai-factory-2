# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| colorPrimary | #1B4332 | #52B788 |
| colorPrimaryContainer | #D8F3DC | #081C15 |
| colorOnPrimary | #FFFFFF | #081C15 |
| colorOnPrimaryContainer | #1B4332 | #B7E4C7 |
| colorSecondary | #BC6C25 | #F4A261 |
| colorSecondaryContainer | #FFE8D6 | #3D2817 |
| colorOnSecondary | #FFFFFF | #1A1208 |
| colorOnSecondaryContainer | #5C3D1E | #FFDDB8 |
| colorSurface | #FFFBF7 | #121212 |
| colorSurfaceContainerLow | #F5F0EB | #1E1E1E |
| colorSurfaceContainer | #EFEBE6 | #2A2A2A |
| colorSurfaceContainerHigh | #E8E4DF | #363636 |
| colorOnSurface | #1C1B1F | #E6E1E5 |
| colorOnSurfaceVariant | #49454F | #CAC4D0 |
| colorOutline | #79747E | #938F99 |
| colorOutlineVariant | #CAC4D0 | #49454F |
| colorError | #BA1A1A | #FFB4AB |
| colorOnError | #FFFFFF | #690005 |
| colorErrorContainer | #FFDAD6 | #93000A |
| colorOnErrorContainer | #410002 | #FFDAD6 |
| colorSuccess | #2D6A4F | #95D5B2 |
| colorOnSuccess | #FFFFFF | #081C15 |
| colorWarning | #9A6700 | #FFD666 |
| colorStarFilled | #E9A319 | #FBBF24 |
| colorStarEmpty | #CAC4D0 | #49454F |
| colorBadgeOutOfStock | #49454F | #E6E1E5 |
| colorBadgeSale | #BC6C25 | #F4A261 |
| colorScrim | #00000080 | #000000B3 |
| colorShadow | #0000001A | #00000040 |
| colorFocusRing | #1B4332 | #52B788 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| displayLarge | 57.0 | 400 | 64.0 |
| displayMedium | 45.0 | 400 | 52.0 |
| displaySmall | 36.0 | 400 | 44.0 |
| headlineLarge | 32.0 | 600 | 40.0 |
| headlineMedium | 28.0 | 600 | 36.0 |
| headlineSmall | 24.0 | 600 | 32.0 |
| titleLarge | 22.0 | 600 | 28.0 |
| titleMedium | 16.0 | 600 | 24.0 |
| titleSmall | 14.0 | 600 | 20.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| bodySmall | 12.0 | 400 | 16.0 |
| labelLarge | 14.0 | 600 | 20.0 |
| labelMedium | 12.0 | 600 | 16.0 |
| labelSmall | 11.0 | 600 | 16.0 |
| priceLarge | 24.0 | 700 | 32.0 |
| priceMedium | 18.0 | 700 | 24.0 |
| priceSmall | 14.0 | 600 | 20.0 |
| priceStrikethrough | 14.0 | 400 | 20.0 |
| specKey | 12.0 | 600 | 16.0 |
| specValue | 14.0 | 400 | 20.0 |

Spacing scale: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80 dp. Corner radii: 0, 4, 8, 12, 16, 24, 999 dp.

## Shared widgets
- **AppShell**: Root scaffold with Material 3 NavigationBar (Home, Products, Cart). Badge on Cart tab shows line-item count from CartNotifier. Respects safe areas; selected tab uses colorPrimary. Minimum 48dp tap targets on all nav destinations. Semantic labels: Home, Browse products, Shopping cart with N items.
- **LumenAppBar**: PreferredSize app bar with optional back, title (titleLarge), optional trailing actions (search, filter). Uses colorSurface and colorOnSurface. Leading back button min 48x48dp with Semantics label Go back.
- **ProductCard**: Vertical card: 1:1 image (BoxFit.cover, semantic label product name), brand (labelSmall, colorOnSurfaceVariant), name (titleSmall, max 2 lines), price row (PriceDisplay), optional OutOfStockBadge or SaleBadge. Entire card tappable min height including padding 48dp effective target. Elevation 1, radius 12dp, padding spacing 12.
- **CategoryTile**: Grid tile: icon or thumbnail 64dp, category label titleSmall centered. Min tap 48dp; semantics: Browse {category name}. Background colorSurfaceContainerLow, radius 12dp.
- **FeaturedProductCarousel**: Horizontal ListView of ProductCard variant (width 160dp) with page dots optional. Semantics: Featured products carousel.
- **SearchField**: TextField with search icon, hint Search by name, SKU, or brand, clear button when non-empty. Min height 48dp. Debounce 300ms before filter apply. Semantics: Product search.
- **FilterSortBar**: Row of FilterChip (active filter count) and SortChip opening FilterSortBottomSheet. Each chip min 48dp height.
- **FilterSortBottomSheet**: Modal bottom sheet (not a route): sections Price range (GBP sliders in pence), Brand multi-select, Category, Wattage multi-select, Finish/color multi-select, In stock only switch, Sort radio (price low/high, newest, popularity). Apply and Reset filters actions min 48dp. Uses colorSurfaceContainerHigh.
- **PriceDisplay**: Formats integer pence to en-GB GBP string via intl (e.g. £24.99). Shows sale price in priceMedium colorPrimary; list price strikethrough priceStrikethrough when compareAtPriceCents present. Semantics include full price text.
- **OutOfStockBadge**: Pill badge labelMedium on colorBadgeOutOfStock with onPrimary contrast text Out of stock. Used on cards and detail.
- **SaleBadge**: Pill badge Sale on colorBadgeSale when item on promotion.
- **StarRatingSummary**: Row of 5 StarRatingIcon (filled/empty/half), numeric average bodyMedium, review count link bodySmall. Semantics: Rated X out of 5 stars, Y reviews.
- **StarRatingIcon**: Icon 20dp colorStarFilled or colorStarEmpty; semantic hidden when part of summary.
- **VariantChipGroup**: Wrap of ChoiceChip for variant axes (finish, wattage, CCT). Selected: colorPrimaryContainer; disabled+OOS: strikethrough label and colorOutline. Min 48dp height per chip. On select updates ProductDetailNotifier selectedVariantId.
- **LightingSpecsTable**: Two-column list showing only non-null spec fields from domain: Product Name, SKU, Wattage, Lumens, Color Temperature, Light Type, Voltage, Dimmable, Material, Finish, Dimensions, IP Rating, Bulb Included, Installation Type. specKey left, specValue right; divider colorOutlineVariant.
- **ReviewListItem**: Avatar initial, author titleSmall, date bodySmall, StarRatingSummary compact, body bodyMedium max 4 lines with Read more on detail preview.
- **ImageGallery**: PageView hero 4:3, dot indicators, pinch optional phase 2. Semantics per image: {product name} image N of M.
- **PrimaryButton**: FilledButton full-width min height 48dp, labelLarge colorOnPrimary. Loading state shows CircularProgressIndicator. Used for Add to cart, Apply filters, Retry.
- **SecondaryButton**: OutlinedButton min 48dp for secondary actions e.g. View all reviews.
- **QuantityStepper**: Row: IconButton decrease (48dp), quantity label titleMedium center min width 48dp, IconButton increase. Decrease disabled at qty 1 if remove is separate; increase capped by available stock in demo or soft max 99. Semantics: Quantity N.
- **CartLineItem**: ListTile-style row: thumbnail 56dp, productName titleSmall, variantLabel bodySmall, PriceDisplay unit, QuantityStepper, IconButton delete 48dp Semantics Remove {name} from cart.
- **EmptyStateView**: Centered illustration placeholder, headlineSmall title, bodyMedium message, optional PrimaryButton or TextButton action. Used for empty catalog, empty search, empty cart, empty reviews.
- **ErrorStateView**: Icon error colorError, title Could not load, body message from error, PrimaryButton Retry calling notifier refresh. For API M2 failures offer offline mock fallback note in debug only.
- **LoadingStateView**: Center CircularProgressIndicator colorPrimary with optional Shimmer placeholders on listing grid.
- **SnackbarCartConfirmation**: After add to cart: Added to cart with action View cart navigating to /cart.

## Screens
### SCR-01 HomeScreen (`/`)
Entry point for guest shoppers: top-level category taxonomy grid, featured product carousel, and quick search that forwards query to product listing. M1 loads categories and featured from LocalCatalogDataSource; M2 uses CatalogRepository getHome when API healthy.
- Components: AppShell, LumenAppBar, SearchField, CategoryTile, FeaturedProductCarousel, ProductCard, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading: shimmer or LoadingStateView while HomeNotifier AsyncLoading, success: category grid 2 columns spacing 16, featured carousel below hero title headlineSmall Shop by room, empty: EmptyStateView No categories available with Retry if seed empty, error: ErrorStateView with Retry; M2 may silently fall back to mock per NFR-06 when configured
- Stories: US-001, US-002, US-006

### SCR-02 ProductListingScreen (`/products`)
Scrollable catalog with product cards, inline search, filter/sort bottom sheet, and category context from go_router query params (categorySlug, q). ProductListNotifier holds filter state and sort. Serves browse, search, filter, and sort for guest demo.
- Components: AppShell, LumenAppBar, SearchField, FilterSortBar, FilterSortBottomSheet, ProductCard, OutOfStockBadge, SaleBadge, PriceDisplay, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading: grid skeleton 2 columns, success: infinite-style ListView or GridView of ProductCard; active filters shown as removable InputChips below search, empty_search: EmptyStateView No products match your search with Clear search restoring full list, empty_filters: EmptyStateView No products match these filters with Reset filters, error: ErrorStateView Retry refreshes ProductListNotifier
- Stories: US-001, US-002, US-003, US-006

### SCR-03 ProductDetailScreen (`/products/:productId`)
Full product detail: gallery, variant selection, price/SKU/stock per variant, lighting specifications, ratings summary, reviews preview with link to full list, add to cart with OOS guard. ProductDetailNotifier loads by id and tracks selectedVariantId.
- Components: LumenAppBar, ImageGallery, PriceDisplay, OutOfStockBadge, VariantChipGroup, LightingSpecsTable, StarRatingSummary, ReviewListItem, SecondaryButton, PrimaryButton, SnackbarCartConfirmation, LoadingStateView, ErrorStateView
- States: loading: hero shimmer and spec placeholders, success: sticky bottom bar PrimaryButton Add to cart enabled when variant in stock; disabled with label Out of stock when OOS, error: ErrorStateView product not found or network error with Retry and back navigation, add_blocked: PrimaryButton disabled semantics explains variant out of stock; no cart mutation
- Stories: US-004, US-005, US-006

### SCR-04 ProductReviewsScreen (`/products/:productId/reviews`)
Paginated full review list and aggregate star summary for a product. ReviewsNotifier paginates listProductReviews; M1 from mock, M2 from API when integrated.
- Components: LumenAppBar, StarRatingSummary, ReviewListItem, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading: first page skeleton list, success: ListView with load-more at scroll end; header shows aggregate rating, empty: EmptyStateView No reviews yet, error: ErrorStateView Retry
- Stories: US-004, US-006

### SCR-05 CartScreen (`/cart`)
In-memory session cart: line items with name, variant label, unit price snapshot in pence GBP, quantity steppers, remove, subtotal. No checkout in demo run. CartNotifier Map keyed by variantId.
- Components: AppShell, LumenAppBar, CartLineItem, QuantityStepper, PriceDisplay, PrimaryButton, EmptyStateView
- States: empty: EmptyStateView Your cart is empty with Browse products navigating to /products, success: ListView of CartLineItem, bottom summary card subtotal label titleMedium, grand total priceLarge; checkout button visible but demo shows Coming in full MVP snackbar or disabled with tooltip, success_mutation: immediate recalc on qty change or remove without network
- Stories: US-005

### SCR-06 AppShellHost (`shell`)
Non-leaf shell wrapping tab routes Home, Products, Cart within six-screen budget. go_router StatefulShellRoute or indexed stack; filter UI remains modal on SCR-02 not a separate route.
- Components: AppShell
- States: success: bottom nav visible on SCR-01 SCR-02 SCR-05, hidden: full-bleed SCR-03 SCR-04 use LumenAppBar back only without bottom nav or with nav hidden per UX choice consistent on emulator
- Stories: US-001, US-005

## Navigation
- SCR-01 → SCR-02: Tap category CategoryTile navigates to /products?categorySlug={slug}
- SCR-01 → SCR-02: Submit SearchField navigates to /products?q={encodedQuery}
- SCR-01 → SCR-03: Tap ProductCard in featured carousel go_router push /products/{productId}
- SCR-01 → SCR-02: AppShell Products tab to /products
- SCR-01 → SCR-05: AppShell Cart tab to /cart
- SCR-02 → SCR-03: Tap ProductCard push /products/{productId}
- SCR-02 → SCR-02: FilterSortBar opens FilterSortBottomSheet modal; Apply updates query state in place
- SCR-02 → SCR-01: AppShell Home tab to /
- SCR-02 → SCR-05: AppShell Cart tab to /cart
- SCR-03 → SCR-04: Tap View all reviews or review count push /products/{productId}/reviews
- SCR-03 → SCR-05: SnackbarCartConfirmation View cart or after add optional icon in app bar if present
- SCR-03 → SCR-02: System back or LumenAppBar back pops to listing
- SCR-04 → SCR-03: Back pops to product detail
- SCR-05 → SCR-02: Empty state Browse products or AppShell Products tab
- SCR-05 → SCR-01: AppShell Home tab
- SCR-05 → SCR-03: Optional tap product name on line item if linked in implementation

## Accessibility
- All interactive controls minimum 48x48dp touch target including IconButtons, chips, nav bar items, and stepper buttons.
- Text contrast minimum WCAG 2.1 AA: colorOnSurface on colorSurface ≥4.5:1 body text; colorOnPrimary on colorPrimary ≥4.5:1; colorOnSurfaceVariant used only for non-essential secondary text ≥4.5:1 on surface.
- Every product and category image has Semantics label describing product or category name; decorative hero backgrounds excludedWithSemantics.
- SearchField, filters, sort, add to cart, quantity steppers, and delete cart line expose clear English en-GB accessibility labels and hints where action is non-obvious.
- StarRatingSummary announces aggregate rating and review count for screen readers.
- VariantChipGroup announces selected variant and disabled out-of-stock state.
- Support system font scaling up to 200% without clipping critical actions; use maxLines with ellipsis on titles only, not on prices.
- Focus order follows visual top-to-bottom; modal bottom sheet traps focus and announces title Filters and sort.
- Error and empty states use live region or SemanticsService announce for dynamic search no results.
- PriceDisplay semantics speak full GBP amounts including pence to avoid ambiguous truncated text.