# Design system

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #2563EB | #60A5FA |
| primary_variant | #1D4ED8 | #93C5FD |
| secondary | #0D9488 | #2DD4BF |
| background | #F8FAFC | #0F172A |
| surface | #FFFFFF | #1E293B |
| surface_variant | #F1F5F9 | #334155 |
| text_primary | #0F172A | #F8FAFC |
| text_secondary | #475569 | #CBD5E1 |
| text_on_primary | #FFFFFF | #0F172A |
| border | #E2E8F0 | #475569 |
| error | #DC2626 | #FCA5A5 |
| warning | #D97706 | #FCD34D |
| success | #059669 | #6EE7B7 |
| disabled | #94A3B8 | #64748B |
| scrim | #00000066 | #00000099 |
| image_placeholder | #E2E8F0 | #334155 |
| banner_overlay | #0F172A80 | #00000080 |
| availability_in_stock | #059669 | #6EE7B7 |
| availability_low_stock | #D97706 | #FCD34D |
| availability_out_of_stock | #DC2626 | #FCA5A5 |
| discount | #7C3AED | #C4B5FD |

## Typography
| Style | Size | Weight | Line height |
|---|---|---|---|
| display | 28.0 | 700 | 36.0 |
| headline | 22.0 | 600 | 28.0 |
| title | 18.0 | 600 | 24.0 |
| body | 16.0 | 400 | 24.0 |
| body_emphasis | 16.0 | 600 | 24.0 |
| label | 14.0 | 500 | 20.0 |
| caption | 12.0 | 400 | 16.0 |
| price | 20.0 | 700 | 28.0 |
| price_strike | 14.0 | 400 | 20.0 |
| button | 16.0 | 600 | 24.0 |
| overline | 11.0 | 600 | 16.0 |

Spacing scale: 4, 8, 12, 16, 20, 24, 32, 48, 64 dp. Corner radii: 4, 8, 12, 16, 24 dp.

## Shared widgets
- **ShopEaseAppBar**: Material 3 AppBar using surface background, text_primary title, optional leading back (min 48dp), trailing actions (search, cart with badge, account) each min 48×48dp with Semantics labels. Cart badge shows item count from CartNotifier.
- **ShopEaseBottomNav**: Four-tab NavigationBar (Home, Search, Cart, Account) bound to go_router ShellRoute; selected state uses primary; labels use label typography; min 48dp tap height per destination.
- **PrimaryButton**: FilledButton using primary background and text_on_primary; min height 48dp, horizontal padding spacing 24; button typography; Semantics button role with explicit label.
- **SecondaryButton**: OutlinedButton with primary border and text_primary label; min 48dp; for secondary actions (Continue shopping, Sign in).
- **TextLinkButton**: TextButton for inline legal links, Forgot password, and Remove item; min 48dp touch padding via TapTargetSize/shrinkWrap false; primary color text.
- **ProductCard**: Grid/list tile: ProductImage, name (title, max 2 lines), brand (caption), PriceText, AvailabilityBadge, optional wishlist IconButton (48dp). Entire card tappable to product detail. Semantics merges name, price, availability.
- **ProductImage**: Aspect-ratio image (1:1 list, 4:3 detail) with corner radius 12, image_placeholder fill, BoxFit.cover, required semanticLabel with product name.
- **PriceText**: Formats integer minor units (cents) + ISO 4217 USD as $X.XX using int math only; price typography; optional strikethrough variant for compare-at; Semantics announces full currency phrase.
- **MoneySummaryRow**: Label/value row for subtotal, discount, shipping, estimated tax, total using body/label styles; total uses price typography; used in cart footer and checkout review.
- **AvailabilityBadge**: Pill chip showing In stock, Low stock, or Out of stock with token colors availability_*; caption typography; never color-only—always includes text.
- **CategoryChip**: Tappable chip for Clothing, Electronics, Home & Kitchen, Beauty, Sports & Outdoors; surface_variant fill, border, min 48dp when standalone; navigates to search with category filter.
- **BannerCarousel**: Horizontal PageView of promo banners from GET /home; 16:9 images with banner_overlay gradient, headline on banner; page indicators; auto Semantics for each banner title.
- **SectionHeader**: Row with headline title and optional See all TextLinkButton (48dp); used for Featured, New arrivals, Categories on home.
- **HorizontalProductList**: Horizontal ListView of compact ProductCard variants for featured and new arrivals sections.
- **SearchBarField**: TextField with search icon, hint Search products, submit on keyboard action; min 48dp height; label Search; clear button when non-empty.
- **SortFilterBar**: Row of FilterChip buttons: Sort (bottom sheet: price low-high, price high-low, newest) and Filters (opens FilterBottomSheet); each chip min 48dp.
- **FilterBottomSheet**: Modal sheet for price range slider, multi-select category, brand (8–12 seeded), availability (in stock, low stock, out of stock); Apply and Clear all Primary/Secondary buttons min 48dp.
- **QuantityStepper**: Minus/plus IconButtons in 48dp containers with quantity label; disables plus at max stock; announces quantity changes.
- **CartLineItem**: Row: thumbnail, name, unit price snapshot (cents USD), QuantityStepper, line total, remove control; min row height 72dp; out-of-stock line shows error caption and blocks checkout.
- **WishlistToggle**: Heart IconButton 48dp; filled when wishlisted; guest persists locally, signed-in via API; Semantics Add to wishlist / Remove from wishlist.
- **AuthTextField**: Email/password/name fields with validation messages, obscure toggle on password, error color for field errors; min 56dp touch height.
- **TabLoginRegister**: TabBar with Login and Register tabs on AuthScreen; indicator primary; tab min 48dp.
- **CheckoutStepperHeader**: Linear step indicator: Shipping, Review & coupon, Payment; current step highlighted primary.
- **AddressForm**: US-only fields: full name, email, phone, address1, address2 optional, city, state (dropdown US contiguous), ZIP; client validation before quote; uses AuthTextField styling.
- **CouponField**: Row: text field for single coupon code, Apply button 48dp; shows applied code chip with remove; inline error text for invalid, expired, minimum not met, excluded items, stacking blocked.
- **OrderStatusStepper**: Horizontal stepper shopper labels Processing → Shipped → Delivered; maps server paid/fulfilled→processing, fulfilled+tracking→shipped, delivered→delivered; current step primary, future steps disabled color.
- **TrackingInfoCard**: Surface card showing carrier name and tracking number when status shipped or delivered; copy-to-clipboard icon 48dp with Semantics Copy tracking number.
- **LoadingStateView**: Centered CircularProgressIndicator primary with optional caption; liveRegion for screen readers.
- **EmptyStateView**: Illustration placeholder, headline, body, optional PrimaryButton CTA; used for empty cart, wishlist, orders, search results.
- **ErrorStateView**: Error icon error color, message body, Retry PrimaryButton 48dp; optional Sign in CTA for auth-gated screens.
- **GuestMergeBanner**: Info banner after login when guest cart replaced merged cart per API; body explains items combined or guest cart applied fallback.
- **WishlistImportDialog**: One-time alert dialog on login/register when local guest wishlist non-empty: Import favorites / Not now; Primary and Secondary 48dp.
- **SupportForm**: Fields: name, email, subject, message (required); Send PrimaryButton; success shows confirmation banner; copy states response within 1–2 business days.
- **LegalDocumentBody**: Scrollable static markdown/plain text from lib/core/legal for Privacy Policy or Terms of Sale; title headline typography.
- **MockPaymentCard**: Demo UI styled like PaymentIntent stub: order summary, Pay now PrimaryButton, Cancel SecondaryButton; no card fields; disclaimer caption demo payment only.
- **OrderConfirmationHeader**: Success icon success color, headline Thank you, order number display title typography, body with email receipt copy for demo.
- **ExpandableOrderCard**: Order history list tile: order number, date, total PriceText, status label; expands to show line items, address summary, OrderStatusStepper, TrackingInfoCard when applicable.

## Screens
### SCR-01 AuthScreen (`/auth`)
Register and log in with email/password tabs; links to forgot password and legal documents; on success stores JWT via flutter_secure_storage and triggers cart merge and optional wishlist import.
- Components: ShopEaseAppBar, TabLoginRegister, AuthTextField, PrimaryButton, TextLinkButton, LoadingStateView, ErrorStateView, GuestMergeBanner, WishlistImportDialog
- States: loading, error, success_idle, validation_error
- Stories: US-001, US-003, US-006

### SCR-02 PasswordResetScreen (`/auth/password-reset`)
Mock forgot-password flow: step 1 submit registered email shows demo sent confirmation; step 2 enter and confirm new password meeting registration rules; no real email delivery.
- Components: ShopEaseAppBar, AuthTextField, PrimaryButton, SecondaryButton, TextLinkButton, LoadingStateView, ErrorStateView
- States: email_step, email_sent_confirmation, new_password_step, loading, error, success
- Stories: US-002

### SCR-03 HomeScreen (`/home`)
Merchandised storefront entry: promotional banners, featured products, new arrivals, and category chips for seeded categories; primary tab in bottom nav.
- Components: ShopEaseBottomNav, ShopEaseAppBar, BannerCarousel, SectionHeader, HorizontalProductList, ProductCard, CategoryChip, LoadingStateView, ErrorStateView, SearchBarField
- States: loading, error, success, partial_error_sections
- Stories: US-004

### SCR-04 SearchResultsScreen (`/search`)
Keyword catalog discovery with sort (price low/high, newest) and filters (price range, category, brand, availability); shows USD prices from integer cents; bottom nav Search tab.
- Components: ShopEaseBottomNav, ShopEaseAppBar, SearchBarField, SortFilterBar, FilterBottomSheet, ProductCard, PriceText, AvailabilityBadge, WishlistToggle, LoadingStateView, EmptyStateView, ErrorStateView
- States: loading, empty, error, success, filter_active
- Stories: US-005

### SCR-05 ProductDetailScreen (`/products/:id`)
M1 baseline detail extended with availability UX: blocks or warns add-to-cart when out of stock; wishlist toggle; navigates from home, search, wishlist.
- Components: ShopEaseAppBar, ProductImage, PriceText, AvailabilityBadge, PrimaryButton, SecondaryButton, WishlistToggle, QuantityStepper, LoadingStateView, ErrorStateView
- States: loading, error, success, out_of_stock
- Stories: US-005, US-006, US-003

### SCR-06 CartScreen (`/cart`)
Guest local or signed-in API cart with line items, quantities, subtotal; merge on login; proceed to checkout when in stock; bottom nav Cart tab.
- Components: ShopEaseBottomNav, ShopEaseAppBar, CartLineItem, MoneySummaryRow, PrimaryButton, SecondaryButton, EmptyStateView, LoadingStateView, ErrorStateView, GuestMergeBanner
- States: loading, empty, error, success, checkout_blocked_stock
- Stories: US-003, US-007

### SCR-07 WishlistScreen (`/wishlist`)
Saved favorites: local persistence for guests, API sync when signed in; add/remove; navigate to product detail; reachable from account and product cards.
- Components: ShopEaseAppBar, ProductCard, WishlistToggle, PrimaryButton, EmptyStateView, LoadingStateView, ErrorStateView, WishlistImportDialog
- States: loading, empty, error, success, guest_local, signed_in_synced
- Stories: US-006

### SCR-08 CheckoutScreen (`/checkout`)
Stepped checkout: US shipping/contact address, order review with line snapshots, flat shipping or free above threshold, estimated tax after discounts, single coupon apply with server quote recalc.
- Components: ShopEaseAppBar, CheckoutStepperHeader, AddressForm, CartLineItem, MoneySummaryRow, CouponField, PrimaryButton, SecondaryButton, TextLinkButton, LoadingStateView, ErrorStateView
- States: loading_quote, address_step, review_step, error, coupon_error_invalid, coupon_error_expired, coupon_error_minimum, coupon_error_excluded, coupon_error_stacking, success_ready_payment
- Stories: US-007, US-008, US-012

### SCR-09 MockPaymentScreen (`/checkout/payment`)
Demo payment stub: POST order then complete-mock-payment; Pay now without card data; cancel releases reservation; on success navigates to confirmation with order number.
- Components: ShopEaseAppBar, CheckoutStepperHeader, MockPaymentCard, MoneySummaryRow, PrimaryButton, SecondaryButton, LoadingStateView, ErrorStateView, OrderConfirmationHeader
- States: loading, ready, processing, error, cancelled, success_confirmation
- Stories: US-009

### SCR-10 OrderConfirmationScreen (`/checkout/confirmation/:orderId`)
Post-purchase confirmation showing human-readable order number, total, and CTAs to order history or continue shopping.
- Components: ShopEaseAppBar, OrderConfirmationHeader, MoneySummaryRow, PrimaryButton, SecondaryButton
- States: loading, error, success
- Stories: US-009

### SCR-11 AccountScreen (`/account`)
Signed-in hub: profile email, links to orders and wishlist, embedded SupportForm and support email, legal links, log out, delete account; guests see sign-in prompt.
- Components: ShopEaseBottomNav, ShopEaseAppBar, PrimaryButton, SecondaryButton, TextLinkButton, SupportForm, ErrorStateView, LoadingStateView
- States: guest_prompt, signed_in, loading, error, support_success, delete_confirm_dialog
- Stories: US-001, US-010, US-012

### SCR-12 OrderHistoryScreen (`/orders`)
Signed-in order list most recent first; guest redirect to auth; expandable order cards show detail, status stepper, and tracking without separate detail route.
- Components: ShopEaseAppBar, ExpandableOrderCard, OrderStatusStepper, TrackingInfoCard, PriceText, EmptyStateView, LoadingStateView, ErrorStateView, PrimaryButton
- States: guest_redirect, loading, empty, error, success, expanded_detail
- Stories: US-010, US-011

## Navigation
- SCR-03 → SCR-04: Tap bottom nav Search or AppBar search action → /search
- SCR-03 → SCR-06: Tap bottom nav Cart or cart icon with badge → /cart
- SCR-03 → SCR-11: Tap bottom nav Account → /account
- SCR-03 → SCR-05: Tap featured/new arrival ProductCard → push /products/:id
- SCR-03 → SCR-04: Tap CategoryChip → /search?category=:slug
- SCR-03 → SCR-04: Submit SearchBarField on home → /search?q=:query
- SCR-04 → SCR-05: Tap ProductCard → push /products/:id
- SCR-04 → SCR-03: Tap bottom nav Home → /home
- SCR-05 → SCR-06: Tap Add to cart → snackbar optional then user opens cart
- SCR-05 → SCR-07: WishlistToggle on → item saved; user opens /wishlist from account
- SCR-06 → SCR-08: Tap Checkout PrimaryButton when cart non-empty and stock valid → /checkout
- SCR-06 → SCR-01: Tap Sign in to sync cart (optional CTA) → /auth
- SCR-01 → SCR-02: Tap Forgot password TextLinkButton → /auth/password-reset
- SCR-01 → SCR-12: Tap Privacy Policy or Terms TextLinkButton → push /legal?document=privacy|terms (LegalDocumentScreen implemented as route overlay using LegalDocumentBody; not counted as 13th shopper screen—content route shares SCR-11 legal links)
- SCR-02 → SCR-01: After successful reset tap Back to login → /auth
- SCR-01 → SCR-03: Successful login/register → go_router redirect /home with cart merge
- SCR-08 → SCR-09: Continue to payment on valid address and quote → /checkout/payment
- SCR-08 → SCR-06: AppBar back → pop to /cart
- SCR-09 → SCR-10: Mock payment success → replace with /checkout/confirmation/:orderId
- SCR-09 → SCR-08: Cancel payment → pop to checkout review
- SCR-10 → SCR-12: View orders → /orders (requires signed in)
- SCR-10 → SCR-03: Continue shopping → /home
- SCR-11 → SCR-12: Tap Order history row → /orders
- SCR-11 → SCR-07: Tap Wishlist → /wishlist
- SCR-11 → SCR-01: Guest tap Sign in → /auth
- SCR-11 → SCR-03: Log out success → /home guest experience
- SCR-12 → SCR-01: Guest opens /orders → redirect prompt Sign in → /auth
- SCR-07 → SCR-05: Tap wishlist ProductCard → /products/:id
- SCR-08 → SCR-12: Footer Terms/Privacy TextLinkButton → /legal?document=terms|privacy
- SCR-11 → SCR-12: Support form submit success stays on account; orders link as above

## Accessibility
- All tappable controls meet minimum 48×48 dp touch targets including IconButtons, chips, ProductCard hit areas, bottom nav items, and stepper controls.
- text_primary on background and surface, and text_on_primary on primary, meet WCAG AA contrast ratio ≥4.5:1 for body text (16sp) and ≥3:1 for large text (price, headlines).
- error, success, and availability badge colors pair with text labels—never convey stock or errors by color alone.
- Every ProductImage, banner, and actionable icon includes a non-empty Semantics label or semanticLabel describing purpose (e.g. product name, Add to cart, Open cart, Remove from wishlist).
- PriceText announces accessible currency strings derived from integer cents (e.g. 12 dollars and 99 cents) rather than raw API integers.
- LoadingStateView, EmptyStateView, and ErrorStateView use Semantics liveRegion or assertive announcements when async state changes.
- OrderStatusStepper exposes current step and step names to screen readers; TrackingInfoCard fields are focusable with copy action labeled.
- Auth and AddressForm fields associate validation errors with fields via Semantics for error text.
- SupportForm required fields announce errors on submit failure; success confirmation is announced.
- Text scaling up to 200% must not clip primary CTAs on checkout and payment—use scrollable layouts and flexible line heights from typography tokens.
- Mock payment screen states clearly in Semantics that no card entry is required and payment is demo-only.
- go_router back navigation preserves logical focus order; AppBar back labeled Go back.
- WishlistImportDialog and delete-account confirmation use modal Semantics with title and action buttons ≥48dp.
- FilterBottomSheet traps focus while open and returns focus to Filters chip on close.
- Minimum spacing scale uses 8dp and 16dp for readable tap gaps between dense list items.