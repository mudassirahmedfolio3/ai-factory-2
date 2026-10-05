# ShopEase Mobile Shopping App — Release 2 Product Requirements Document

ShopEase Release 2 expands the existing M1 guest catalog and M2 NestJS catalog API integration into a client-ready Android demo with shopper depth: accounts, a merchandised home experience, search with sort and filters, guest and signed-in carts (merge on login), API-backed wishlist for signed-in users, full US-only checkout with flat shipping, estimated tax, single-use coupons, mock payment (no Stripe), order history and tracking with carrier details, in-app support, password-reset stub, and lightweight legal screens. All new delivery is planned under milestone M3 “Release 2 — shopper depth” with work items continuing from WI-010. Prices use integer minor units (cents) and ISO 4217 USD; order lines snapshot product name and unit price at purchase; order status follows pending_payment → paid → fulfilled → delivered (plus cancelled and refunded where applicable). Demo-safe operations only: mock PaymentIntent-style pay step marks orders paid on the server without real processor keys or webhooks.

## Personas
### First-time Guest Shopper
An Android user who discovers ShopEase without an account, browses the catalog, may add items to a device-local cart and wishlist, and can complete a purchase path that does not require registration unless they choose to sign up for persistence.
- Explore products from home, categories, search, and filters without creating an account
- Build a guest cart and proceed toward checkout with clear shipping and tax estimates
- Optionally register later and not lose cart or wishlist items

### Returning Signed-in Customer
A repeat shopper who registers or logs in to persist cart, wishlist, and order history across sessions and devices via the API.
- Log in securely and stay signed in with tokens stored safely on device
- See merged cart contents after login when a guest cart existed
- Track past orders and order status from order history

### Deal-seeking Shopper
A price-conscious buyer who compares products by category, brand, price, and availability and applies a single coupon code at checkout.
- Sort and filter the catalog to find in-stock items in budget
- Apply one valid promo code and see discounted totals before paying
- Understand why a coupon was rejected (expired, below minimum, exclusions)

### Post-purchase Customer
A buyer who needs visibility into order progress and a straightforward way to contact support after placing an order.
- View order history and status progression processing → shipped → delivered
- See carrier name and tracking number when an order has shipped or delivered
- Reach support via email or an in-app form with clear response-time expectations

## User stories
### US-001 Register, log in, and log out (must)
As a shopper, I want to create an account, sign in, and sign out with secure session handling, so that I can persist cart, wishlist, and orders across sessions while keeping my credentials protected.

- **Given** I am on the registration screen and enter a unique valid email and a password of at least 8 characters containing at least one letter and one number **when** I submit registration **then** the server creates my account with the password stored using bcrypt or argon2 hashing (never plaintext), returns an auth token, and I can shop immediately without mandatory email verification
- **Given** I have a registered account **when** I log in with correct email and password **then** I receive a JWT (or equivalent) auth token, the app stores it in secure device storage (e.g. flutter_secure_storage), and subsequent API calls include the token until I log out
- **Given** I am signed in **when** I tap log out **then** the auth token is cleared from secure storage, I am returned to a guest-appropriate experience, and protected API calls no longer use the previous session
- **Given** I am on registration or account settings **when** I open linked legal content **then** I can navigate to in-app Privacy Policy and Terms of Sale placeholder screens reachable from registration and account flows

### US-002 Reset password via in-app mock flow (should)
As a signed-in or returning shopper who forgot my password, I want to reset my password through an in-app flow backed by a mock API, so that I can regain access in the demo without real email delivery.

- **Given** I am on the forgot-password entry screen **when** I submit a registered email address **then** I see a confirmation message that reset instructions were sent (demo copy may note production would email a link) and I can proceed to enter a new password without actual email delivery
- **Given** I completed the email step for a registered account in the mock reset flow **when** I enter a new password meeting the same rules as registration (minimum 8 characters, at least one letter and one number) and confirm it **then** the mock API accepts the change and I can log in with the new password on the next login attempt

### US-003 Guest cart and merge on login (must)
As a guest or returning shopper, I want to shop with a guest cart and have it merge into my account cart when I log in, so that I do not lose items I already selected.

- **Given** I am browsing as a guest and add products to the cart **when** I view the cart **then** I see line items with product name and unit price in integer USD minor units (cents) displayed correctly, quantities adjustable where in stock, and out-of-stock variants cannot be added or show a clear error
- **Given** I have items in a guest cart and I log into an account that also has cart items, including at least one SKU that exists in both carts **when** login completes **then** the guest cart merges into the account cart by combining quantities for matching product variants and keeping distinct line items for non-matching products, and the unified cart is persisted via the API for the signed-in user
- **Given** merging guest and account carts is not fully implementable in time **when** I log in with a non-empty guest cart **then** the account cart is replaced by the guest cart (documented fallback) rather than leaving two separate carts active
- **Given** I am signed in with items in my API-backed cart **when** I close and reopen the app **then** my cart contents are restored from the server for that user

### US-004 Merchandised home experience (must)
As a shopper, I want a home screen with banners, featured products, new arrivals, and category entry, so that the app feels like a real storefront rather than only a flat product list.

- **Given** I open the app home route **when** the home screen loads **then** I see promotional banners, a featured products section, a new arrivals section, and tappable category entry points aligned to seeded categories (Clothing, Electronics, Home & Kitchen, Beauty, Sports & Outdoors)
- **Given** I am on the home screen **when** I tap a featured product, new arrival, or category entry **then** I navigate to product detail or a filtered product list for that category without errors

### US-005 Search, sort, and filter catalog (must)
As a shopper, I want keyword search with sort and filters on price, category, brand, and availability, so that I can find products quickly in a catalog of roughly 50–100 seeded SKUs.

- **Given** the seeded catalog is loaded from the M2 API baseline **when** I enter a keyword in search and submit **then** I see products whose names or relevant fields match the query, each showing price from integer cents with USD currency code
- **Given** I am viewing search or category product results **when** I choose sort by price (low to high or high to low) or sort by newest **then** the list order updates accordingly and remains stable for the same sort selection
- **Given** I am viewing product results **when** I apply filters for price range, category, brand (from roughly 8–12 seeded brands), and availability (in stock, low stock, out of stock) **then** only products matching all selected filters are shown, and clearing filters restores the broader result set
- **Given** a product variant is out of stock per seed data **when** I view it in list or detail from filtered results **then** availability is clearly indicated and add-to-cart is blocked or warns appropriately

### US-006 Wishlist for guests and signed-in users (should)
As a shopper, I want to save and remove favorite products on a wishlist, so that I can return to items I intend to buy later.

- **Given** I am browsing as a guest **when** I add or remove products on the wishlist **then** changes persist locally on the device only and survive app restarts until I clear app data
- **Given** I am signed in **when** I add or remove wishlist items **then** changes are stored via the ShopEase API and appear after I log in on another session or device
- **Given** I have a non-empty local guest wishlist and I register or log in **when** the app offers a one-time import of local favorites **then** accepting import merges local items into my API wishlist without duplicating the same product variant

### US-007 Checkout with US shipping and estimated tax (must)
As a shopper ready to buy, I want to enter contact and US shipping address, review my order, and see shipping and tax lines, so that I understand total cost before placing an order.

- **Given** I have a non-empty cart and proceed to checkout **when** I enter contact and a valid US shipping address (United States contiguous states acceptable for demo) **then** the order review shows line items with product name and unit price copied at checkout time (integer cents USD), subtotal, optional discount line if a coupon is applied, shipping, estimated tax, and order total in minor units only on the server
- **Given** my order subtotal is below the seeded free-shipping threshold (for example 7500 cents / $75.00) **when** I view the review step **then** a flat standard shipping rate (for example 599 cents / $5.99) is shown as a distinct line
- **Given** my order subtotal meets or exceeds the seeded free-shipping threshold **when** I view the review step **then** shipping is shown as free (zero shipping line or explicit $0.00 shipping)
- **Given** discounts have been applied to the subtotal where applicable **when** I view the review step **then** estimated sales tax is calculated as a simple fixed percentage of the taxable subtotal after discounts (for example 8%) with copy that final tax may vary, and no multi-jurisdiction tax engine is required

### US-008 Apply single coupon at checkout (must)
As a deal-seeking shopper, I want to apply one coupon code validated against seeded promotions, so that I receive eligible discounts with clear errors when invalid.

- **Given** I am on checkout review with a cart meeting a seeded promo’s rules **when** I enter a valid percent-off or fixed-amount-off coupon code that is not expired and meets minimum order value without hitting category or product exclusions **then** the discount is applied, only one coupon is active on the order (no stacking), and totals recalculate using integer minor units
- **Given** I have already applied a coupon to the order **when** I attempt to apply a second coupon **then** the app prevents stacking and shows a clear message that only one code per order is allowed
- **Given** I enter an invalid, expired, below-minimum, or exclusion-violating coupon **when** I apply the code **then** no discount is applied and I see a specific error message (invalid, expired, minimum not met, or excluded items) without placing the order

### US-009 Complete purchase with mock payment (must)
As a shopper on the payment step, I want to pay using a demo pay-now action without real card processing, so that I receive order confirmation suitable for pilots and demos.

- **Given** I completed checkout review with valid address and cart stock available per variant **when** I tap the demo pay-now control on the mock payment step (PaymentIntent stub UI acceptable) **then** no Stripe keys are used, card data is not collected or sent to our server, and the server creates an order in pending_payment then marks it paid for demo purposes without webhooks or external processor calls
- **Given** checkout reserved stock per variant on the server **when** mock payment succeeds **then** the order status becomes paid, order lines retain snapshotted product name and unit price, and I see a confirmation screen with a human-readable order number
- **Given** mock payment fails or is cancelled in the demo flow **when** I abandon or fail the pay step **then** the order does not remain in a paid state and reserved stock is released according to server rules for failed or expired payment

### US-010 View order history (must)
As a signed-in shopper, I want to see a list of my past orders, so that I can review what I bought and open details.

- **Given** I am signed in and have at least one placed order **when** I open order history **then** I see orders sorted with most recent first, each showing order number, date, total in USD from minor units, and high-level status
- **Given** I am a guest who has not signed in **when** I attempt to open order history **then** I am prompted to sign in or register rather than seeing another user’s orders
- **Given** I tap an order in the list **when** the order detail loads **then** I see line items with snapshotted names and unit prices, shipping address summary, and current status

### US-011 Track order status and shipment (must)
As a signed-in shopper, I want to see order status progression and tracking when shipped, so that I know when my purchase is on the way.

- **Given** I open an order in processing (paid/fulfilled demo state mapped to processing label for shoppers) **when** I view order detail **then** I see the status progression processing → shipped → delivered with the current step highlighted and processing orders omit carrier tracking until shipped
- **Given** an order is in shipped or delivered status with seeded demo fulfillment data **when** I view order detail **then** I see carrier name and tracking number in addition to the status progression
- **Given** order statuses on the server follow pending_payment → paid → fulfilled → delivered plus cancelled and refunded **when** the app displays shopper-facing labels **then** paid/fulfilled map to processing, shipped maps to shipped, and delivered maps to delivered in a testable consistent way documented for QA

### US-012 Contact support and legal information (should)
As a shopper, I want an in-app support screen and access to policies, so that I know how to get help and understand terms before buying.

- **Given** I open the support screen from account or help entry **when** the screen loads **then** I see the primary support email (for example support@shopease-demo.com), a simple form to send or simulate a message, and copy stating we aim to respond within one to two business days, with no live chat or phone
- **Given** I submit the support form with required fields completed **when** I tap send **then** the app shows success or simulated-send confirmation without requiring a live mail integration in Release 2
- **Given** I am on checkout, registration, or settings **when** I follow Privacy Policy or Terms of Sale links **then** I open static in-app placeholder screens suitable for demo and early pilot

## Non-functional requirements
- Platform: Flutter 3.x Android-first; the app must run on the Android emulator and pass flutter analyze and flutter test for Release 2 changes.
- Backend: Extend existing NestJS OpenAPI and Prisma PostgreSQL 16 baseline only as needed for auth, carts, wishlist, orders, coupons, and optional read-only admin endpoints; new endpoints must have Jest/Supertest coverage and keep the suite green.
- API scope discipline: at most 24 counted API operations for Release 2 (excluding infrastructure /health and /api/docs-json); include /health in the deployed contract.
- App screen discipline: at most 12 new or materially changed shopper-facing screens for Release 2 (home, search/results, wishlist, checkout steps, payment stub, confirmation, orders, order detail, support, auth flows, legal may share screens where reasonable).
- Money: all prices, discounts, shipping, tax, and totals stored and transmitted as integer minor units with ISO 4217 currency code USD; never use floating-point money on the server.
- Inventory: stock tracked per product variant; checkout reserves stock and failed or expired mock payment releases reservation.
- Orders: order lines snapshot product name and unit price at purchase; later catalog changes must not alter historical orders.
- Security: passwords hashed with bcrypt or argon2; JWT auth for signed-in API access; tokens stored in secure device storage; support account deletion with minimum personal data retained (expose via API/settings as feasible in M3).
- Payments: mock/demo payment only—no Stripe test or live keys, no PaymentIntent creation against Stripe, no Stripe webhooks in Release 2.
- Performance: home, product list, and search results should load within 3 seconds on emulator against local/staging API under normal demo seed size (~50–100 products).
- Accessibility: touch targets and text scaling should not break primary flows (browse, cart, checkout, order history); semantic labels on key actions for screen readers where Flutter supports them.
- Privacy: lightweight Privacy Policy and Terms screens linked from registration, checkout, and settings; optional non-blocking verify-email stub only if implemented—email verification not required to shop.
- Quality gate: complete at least one QA round on milestone M3 before calling Release 2 done; document scope in docs/PRD backlog.
- Notifications: production push notifications out of scope—if touched, log or mock only.

## Out of scope
- Real Stripe PaymentIntents, Stripe SDK card collection, or Stripe webhooks (deferred until production payment readiness).
- Production push notifications (FR-18).
- Full admin panel UI (AR-01–AR-09); optional minimal read-only admin API for orders/products/coupons only if time permits without jeopardizing shopper features.
- Google and Apple social sign-in.
- Guest-accessible server-side order history without authentication.
- Multi-coupon stacking or complex promotion stacking rules.
- Shipping outside the United States, dynamic carrier rate shopping, or multi-jurisdiction tax engines.
- Live chat, phone support, or real email delivery for password reset and support forms in Release 2.
- Email verification required before purchase.
- Replacing or re-planning M1/M2 baseline catalog list, detail, and API client except small deltas required by Release 2 features.
- iOS store release, production deployment hardening, and full legal/compliance review beyond placeholder policy screens.

## Assumptions
- M1 guest catalog UI and M2 NestJS catalog OpenAPI + generated Dart client remain the foundation; Release 2 adds auth, merchandising, discovery, wishlist, checkout, orders, coupons, and support on top.
- Seed catalog includes roughly 50–100 products across Clothing, Electronics, Home & Kitchen, Beauty, and Sports & Outdoors with 8–12 brands and availability states (in stock, low stock, out of stock) sufficient for filters and demos.
- Milestone M3 is titled “Release 2 — shopper depth” and contains only new work items starting at WI-010 (not duplicated M1/M2 items).
- Free shipping threshold and flat rate use seeded configuration (for example $75.00 threshold and $5.99 standard shipping) and estimated tax uses a fixed percentage (for example 8%) on subtotal after discounts.
- Mock payment marks orders paid for demo; shopper-facing status labels align to backend states for QA traceability.
- Signed-in users persist cart and wishlist via API; guests use local cart and local wishlist with merge/import behaviors defined in clarifications.
- Coupon seed data includes expiry, minimum order value, percent and fixed discounts, and optional category/product exclusions; one code per order.
- Docker/docker-compose staging and GitHub Actions patterns from the repo apply; Release 2 does not require new production payment processor accounts.
- Brand/visual identity beyond ShopEase working title may evolve without blocking functional acceptance for M3.
- Optional read-only admin API priority: orders list/detail first, then products, then coupons—JSON/OpenAPI only, no admin UI.

## M3 delivery sign-off (Release 2 backlog)

As of 2026-10-04, milestone M3 “Release 2 — shopper depth” meets the PRD quality gate: one QA round documented in `reports/qa_M3_round1.md`, `flutter analyze` and `flutter test` passing for Release 2 app changes, server tests green via WI-020, staging stack verified with GET `/health` (`getHealth`) through docker-compose smoke scripts and CI, and a reproducible Android emulator demo entry point (`scripts/run-android-emulator-demo.sh`). Scope sign-off is recorded in `docs/backlog.md`; follow-on production hardening (real payments, email delivery, push) stays out of scope above.
