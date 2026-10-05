# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1B2838 | #E8EDF3 |
| onPrimary | #FFFFFF | #0E141C |
| primaryContainer | #DDE4EC | #2A3848 |
| onPrimaryContainer | #1B2838 | #E8EDF3 |
| secondary | #734E00 | #FFCC80 |
| onSecondary | #FFFFFF | #251804 |
| secondaryContainer | #FFF3D6 | #5C3D00 |
| onSecondaryContainer | #2A1F08 | #FFECB3 |
| tertiary | #3D5A80 | #A8C7E7 |
| onTertiary | #FFFFFF | #0F1A28 |
| surface | #FAF8F5 | #121820 |
| onSurface | #1C1B18 | #E8E6E3 |
| surfaceVariant | #EDE8E0 | #2A2F38 |
| onSurfaceVariant | #4A453E | #C8C2B8 |
| background | #FAF8F5 | #0E1218 |
| onBackground | #1C1B18 | #E8E6E3 |
| outline | #79766F | #938F88 |
| outlineVariant | #C9C4BC | #4A4740 |
| error | #BA1A1A | #FFB4AB |
| onError | #FFFFFF | #690005 |
| errorContainer | #FFDAD6 | #93000A |
| onErrorContainer | #410002 | #FFDAD6 |
| success | #1B6E3A | #8FD9A8 |
| onSuccess | #FFFFFF | #0A2E18 |
| warning | #734E00 | #FFCC80 |
| onWarning | #FFFFFF | #251804 |
| cartBadge | #734E00 | #FFCC80 |
| onCartBadge | #FFFFFF | #251804 |
| scrim | #1C1B18 | #000000 |
| inverseSurface | #31302C | #E8E6E3 |
| inverseOnSurface | #F5F3F0 | #1C1B18 |
| stockInStock | #1B6E3A | #8FD9A8 |
| stockLowStock | #734E00 | #FFCC80 |
| stockOutOfStock | #79766F | #938F88 |
| divider | #E0DBD3 | #3A3F48 |
| shadow | #1C1B18 | #000000 |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| displayLarge | 32.0 | 700 | 40.0 |
| displayMedium | 28.0 | 700 | 36.0 |
| headlineLarge | 24.0 | 600 | 32.0 |
| headlineMedium | 20.0 | 600 | 28.0 |
| titleLarge | 18.0 | 600 | 24.0 |
| titleMedium | 16.0 | 600 | 22.0 |
| bodyLarge | 16.0 | 400 | 24.0 |
| bodyMedium | 14.0 | 400 | 20.0 |
| bodySmall | 12.0 | 400 | 16.0 |
| labelLarge | 14.0 | 600 | 20.0 |
| labelMedium | 12.0 | 600 | 16.0 |
| labelSmall | 11.0 | 500 | 14.0 |
| priceLarge | 22.0 | 700 | 28.0 |
| priceMedium | 16.0 | 600 | 22.0 |
| caption | 12.0 | 400 | 16.0 |

Spacing scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 dp. Corner radii: 0, 4, 8, 12, 16, 24, 999 dp.

## Shared widgets
- **LumenAppBar**: Top app bar with Lumen wordmark, optional back, search icon (min 48dp), cart icon with CartBadgeChip showing item count from CartNotifier; semantic labels on all actions.
- **CartBadgeChip**: Circular 20dp min badge using cartBadge/onCartBadge tokens; hides when count zero; Semantics label includes item count.
- **PrimaryButton**: Filled button primary/onPrimary, min height 48dp, full-width on forms; loading shows inline CircularProgressIndicator.
- **SecondaryButton**: Filled secondary/onSecondary for accent CTAs (e.g. Apply coupon); min height 48dp.
- **OutlinedButton**: 1dp outline border, onSurface text; used for secondary actions (Continue shopping, Retry).
- **TextButton**: Text-only actions (Forgot password, View all); min tap target 48dp via padding.
- **ProductCard**: Thumbnail 1:1 aspect, title (max 2 lines), price from pence via MoneyFormatter, optional OOS badge; tap navigates to product detail.
- **ProductGrid**: Responsive 2-column grid with spacing tokens; supports pull-to-refresh on listing screens.
- **HorizontalProductCarousel**: Snap carousel for featured/new arrivals on home; exposes Semantics header per section.
- **CategoryTile**: Square tile with image or icon, category name; min 48dp touch target.
- **SearchBarField**: Read-only tap opens Product Listing with focus; or embedded TextField on listing with debounced query to API.
- **FilterSortBar**: Chip row: Sort bottom sheet, Filters bottom sheet with active filter count badge.
- **FilterBottomSheet**: Multi-select filters: price range slider, brand, category, wattage, finish, availability; Apply/Clear actions.
- **SortBottomSheet**: Radio list: price asc/desc, newest, popularity (seed weight).
- **VariantSelector**: Chip group for finish, wattage, color temperature; updates price, SKU, stock from selected variant.
- **SpecsTable**: Two-column key-value list for lighting attributes (wattage, lumens, CCT, IP, dimmable, dimensions).
- **QuantityStepper**: Minus/plus with 48dp targets; enforces max stock; shows inline error on oversell.
- **MoneyFormatter**: Formats integer GBP pence to major units with £ prefix and 2 decimals; used on all price surfaces.
- **OrderStatusTimeline**: Vertical stepper mapping paid→processing, fulfilled→shipped, delivered; cancelled/refunded as terminal states when seeded.
- **AddressFormUK**: Validated UK mainland fields: name, line1, line2 optional, city, postcode; copy notes standard domestic delivery only.
- **CouponField**: Text field + Apply using SecondaryButton; shows server validation errors; one coupon max.
- **CheckoutSummaryCard**: Line items snapshot, subtotal, shipping, discount, total in pence; matches server preview.
- **MockPaymentPanel**: Demo secure payment UI: no PAN/CVV fields; Pay now / Simulate failure buttons calling confirmMockPayment; explanatory copy.
- **EmptyStateView**: Illustration slot, title, body, optional CTA; used for empty cart, wishlist, orders, search.
- **ErrorStateView**: Icon, message, Retry action; distinguishes network vs validation errors.
- **LoadingSkeleton**: Shimmer placeholders for lists, detail, home carousels.
- **OfflineBanner**: Non-blocking banner when API health fails; home/catalog use local fallback catalog.
- **GuestSignedInBanner**: Inline note on cart/checkout indicating guest session or signed-in persistence.
- **WishlistToggleButton**: Heart icon on product detail/list; guests route to Auth; signed-in calls wishlist API.
- **BottomNavShell**: Optional shell with Home, Categories, Cart, Account tabs; badges on cart.
- **SecureWebView**: FAQ/support WebView with UK privacy-safe settings.
- **SnackbarHost**: App-wide snackbars for add-to-cart, merge cart, coupon applied.

## Screens
### SCR-01 HomeScreen (`/`)
API-backed merchandised entry with banners, featured and new-arrival carousels, category shortcuts, and search entry; falls back to local catalog when health fails.
- Components: LumenAppBar, SearchBarField, HorizontalProductCarousel, CategoryTile, ProductCard, OfflineBanner, LoadingSkeleton, ErrorStateView
- States: loading, success, error, offline_fallback
- Stories: US-001, US-014

### SCR-02 CategoriesScreen (`/categories`)
Browse top-level lighting categories and subcategories; navigate to scoped product listing.
- Components: LumenAppBar, CategoryTile, LoadingSkeleton, ErrorStateView, EmptyStateView
- States: loading, success, empty, error
- Stories: US-001

### SCR-03 ProductListingScreen (`/products`)
Search, filter, and sort catalog; shows OOS badges; query params: q, categoryId, subcategoryId, sort, filters.
- Components: LumenAppBar, SearchBarField, FilterSortBar, FilterBottomSheet, SortBottomSheet, ProductGrid, ProductCard, LoadingSkeleton, EmptyStateView, ErrorStateView
- States: loading, success, empty, error
- Stories: US-002, US-001, US-014

### SCR-04 ProductDetailScreen (`/products/:productId`)
Gallery, variant selection, specs, reviews preview, add-to-cart, wishlist toggle; bundled product imagery.
- Components: LumenAppBar, VariantSelector, SpecsTable, QuantityStepper, PrimaryButton, WishlistToggleButton, MoneyFormatter, LoadingSkeleton, ErrorStateView
- States: loading, success, error, out_of_stock
- Stories: US-003, US-005, US-006, US-014

### SCR-05 CartScreen (`/cart`)
Review server cart lines, update quantities, remove items, view subtotal; guest vs signed-in indicator.
- Components: LumenAppBar, GuestSignedInBanner, QuantityStepper, MoneyFormatter, PrimaryButton, OutlinedButton, EmptyStateView, LoadingSkeleton, ErrorStateView
- States: loading, success, empty, error, stock_validation_error
- Stories: US-005, US-004

### SCR-06 CheckoutScreen (`/checkout`)
UK contact and shipping address, order review, coupon entry, shipping rules and free-delivery threshold copy.
- Components: LumenAppBar, AddressFormUK, CheckoutSummaryCard, CouponField, SecondaryButton, PrimaryButton, MoneyFormatter, LoadingSkeleton, ErrorStateView
- States: loading, success, error, validation_error
- Stories: US-007, US-009, US-005

### SCR-07 MockPaymentScreen (`/checkout/payment`)
Mock secure payment step after checkout preview; stock reserved; retry on failure without duplicate paid orders.
- Components: LumenAppBar, MockPaymentPanel, CheckoutSummaryCard, PrimaryButton, OutlinedButton, ErrorStateView
- States: ready, processing, success, error, cancelled
- Stories: US-008, US-007

### SCR-08 OrderConfirmationScreen (`/checkout/confirmation/:orderId`)
Post-payment confirmation with order number, snapshotted lines, address, totals, estimated UK delivery copy.
- Components: PrimaryButton, CheckoutSummaryCard, MoneyFormatter, OutlinedButton
- States: success, error
- Stories: US-010, US-008

### SCR-09 AuthScreen (`/auth`)
Combined login and register tabs; forgot-password request mode; reset-password mode via query token; triggers guest cart merge on success.
- Components: PrimaryButton, TextButton, OutlinedButton, ErrorStateView, LoadingSkeleton
- States: login, register, forgot_password, reset_password, loading, error, validation_error, success
- Stories: US-004, US-012

### SCR-10 AccountScreen (`/account`)
Profile summary, order history entry, wishlist entry, support link, logout, delete account (GDPR).
- Components: LumenAppBar, PrimaryButton, OutlinedButton, TextButton, ErrorStateView
- States: signed_in, signed_out, loading, error
- Stories: US-004, US-011, US-013, US-006

### SCR-11 OrderHistoryScreen (`/orders`)
Paginated list of past orders for authenticated customers; guests redirected to auth.
- Components: LumenAppBar, OrderStatusTimeline, MoneyFormatter, EmptyStateView, LoadingSkeleton, ErrorStateView
- States: loading, success, empty, error, unauthenticated
- Stories: US-011

### SCR-12 OrderDetailScreen (`/orders/:orderId`)
Order lines with purchase-time snapshots, status timeline, tracking when seeded, totals and shipping address.
- Components: LumenAppBar, OrderStatusTimeline, CheckoutSummaryCard, MoneyFormatter, LoadingSkeleton, ErrorStateView
- States: loading, success, error
- Stories: US-011, US-010

### SCR-13 WishlistScreen (`/wishlist`)
Registered-user wishlist synced via API; add/remove; navigate to product detail.
- Components: LumenAppBar, ProductGrid, ProductCard, WishlistToggleButton, EmptyStateView, LoadingSkeleton, ErrorStateView
- States: loading, success, empty, error, unauthenticated
- Stories: US-006

### SCR-14 SupportScreen (`/support`)
UK customer support contact, hours, phone, email, FAQ WebView; demo catalog disclaimers.
- Components: LumenAppBar, SecureWebView, PrimaryButton, TextButton
- States: success
- Stories: US-013, US-014

## Navigation
- SCR-01 → SCR-03: Tap search bar or submit query from home
- SCR-01 → SCR-02: Tap Shop categories or category shortcut
- SCR-01 → SCR-04: Tap product card or carousel item
- SCR-01 → SCR-05: Tap cart icon in app bar
- SCR-02 → SCR-03: Select category or subcategory
- SCR-03 → SCR-04: Tap product card
- SCR-04 → SCR-05: Add to cart success snackbar or cart icon
- SCR-04 → SCR-09: Wishlist while guest
- SCR-05 → SCR-06: Tap Proceed to checkout
- SCR-05 → SCR-03: Continue shopping
- SCR-06 → SCR-07: Place order / Continue to payment after valid preview
- SCR-07 → SCR-08: Mock payment success
- SCR-07 → SCR-07: Mock payment failure — show error and Retry
- SCR-08 → SCR-01: Continue shopping
- SCR-08 → SCR-11: View orders when signed in
- SCR-09 → SCR-05: Login/register success after cart merge
- SCR-10 → SCR-09: Sign in when signed out
- SCR-10 → SCR-11: Order history menu item
- SCR-10 → SCR-13: Wishlist menu item
- SCR-10 → SCR-14: Customer support menu item
- SCR-11 → SCR-12: Tap order row
- SCR-11 → SCR-09: Guest/unauthenticated access attempt
- SCR-13 → SCR-09: Guest access attempt
- SCR-13 → SCR-04: Tap wishlist product
- SCR-01 → SCR-10: Account tab or profile icon

## Accessibility
- Minimum interactive touch target 48dp on all buttons, steppers, chips, nav icons, and list tiles (expand hit area with padding where visual size is smaller).
- All product, category, and icon images include Semantics labels or excludeFromSemantics when decorative with adjacent text.
- Color contrast at least WCAG 2.1 AA (4.5:1 normal text, 3:1 large text) for all semantic token pairs including secondary/onSecondary and cartBadge/onCartBadge in light and dark themes.
- Support system text scaling up to 200%; layouts use scroll views and do not clip critical actions.
- Focus order follows visual order on forms (checkout, auth, address).
- Error and validation messages exposed to screen readers via live regions.
- Mock payment screen states clearly that card data is not collected on-device or sent to Lumen servers.
- Filter and sort sheets trap focus while open and restore focus on dismiss.
- Order status timeline steps include combined Semantics labels (status name and date when present).
- Cart quantity changes announce updated count and line subtotal.