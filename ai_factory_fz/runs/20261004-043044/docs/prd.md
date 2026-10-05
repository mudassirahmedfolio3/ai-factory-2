# Lumen — Lighting Retail Mobile App: Product Requirements Document (Release 2 / Milestone M3)

Release 2 (Milestone M3 — shopper depth & production catalog) extends the Pass 1 baseline (WI-001–WI-012: Flutter guest catalog with local/API fallback, NestJS /api/v1 health + catalog OpenAPI, Dart client) with registered accounts, guest and signed-in shopping, API-backed home merchandising, search with filters and sorting, registered-user wishlist, UK domestic checkout with simplified shipping, mock secure payment (no Stripe integration in this release), coupon codes for guests and signed-in users, order history and status tracking, customer support, and a production-style lighting catalog of 18–30 SKUs with bundled real product photography sourced per docs/IMAGE_SOURCES.md. All shoppers use one VAT-inclusive B2C price list. Prices are stored as integer minor units (GBP pence) with ISO 4217 currency code GBP. Stock is tracked per product variant; checkout reserves stock and failed or expired mock payment releases it. Carts belong to signed-in users when authenticated; guests use session-scoped carts until login, when cart merge applies. Order status flow: pending_payment → paid → fulfilled → delivered, plus cancelled and refunded (staff/API-only display where seeded; no shopper self-service cancel/return/refund). Order lines snapshot product name and unit price at purchase time. Mock payment follows a secure pattern: no raw card data on server; order marked paid only after successful mock confirmation. Pass 1 work is not replanned; new delivery work starts at WI-013. Quality bar: flutter analyze and flutter test green; Jest/Supertest for new API endpoints; one M3 QA round before Release 2 complete.

## Personas
### Guest Shopper (DIY Homeowner)
A UK homeowner upgrading indoor or ceiling lighting who wants to compare wattage, lumens, and finish quickly and complete a purchase without creating an account.
- Browse categories and featured products on home
- Filter and sort the catalog by price, brand, and lighting specs
- Add variants to cart and check out with UK address and mock payment
- Apply a coupon code at checkout
- Receive order confirmation with order number

### Registered Customer
A repeat buyer who creates an account for a persistent cart, order history, and wishlist synced via API.
- Register, log in, and log out securely
- Merge guest cart into account on login
- Save favorites to wishlist and manage cart across sessions
- View past orders and track status (processing, shipped, delivered)
- Reset password via demo-friendly flow (stub email/deep link acceptable)

### Trade Buyer (Electrician / Small Contractor)
A professional who orders repeat SKUs by brand, wattage, and IP rating using the same app experience as consumers for Release 2.
- Search by SKU, brand, and keywords
- Compare technical specs on product detail (IP rating, dimmable, color temperature)
- Place orders quickly with standard UK shipping rules
- Rely on accurate stock and variant selection

### Internal Catalog / Order Staff (API Consumer)
Operations staff who manage catalog, orders, and promotions via API (and optional minimal admin UI or documented API); full admin panel UI is deferred.
- Maintain seeded catalog and promos consistent with OpenAPI
- Update order statuses for demo tracking flows
- Verify data integrity (prices, stock, no duplicate orders)

## User stories
### US-001 Discover products on home and by category (must)
As a shopper (guest or signed-in), I want to open a merchandised home screen and browse lighting by category and subcategory, so that I can find relevant fixtures and fittings like a specialist UK retailer.

- **Given** the API health check succeeds and home merchandising data is seeded **when** I open the app home screen **then** I see API-backed banners, featured products, new arrivals, and category entry points
- **Given** the API is unavailable or health fails **when** I open the app home screen **then** I see the Pass 1 local/API fallback catalog so I can still browse offline on the Android emulator demo
- **Given** I am on the categories screen **when** I select a category and optional subcategory **then** I see a product listing scoped to that category with image, name, price in GBP (VAT-inclusive), and availability indicator where seed supports it

### US-002 Search, filter, and sort the lighting catalog (must)
As a shopper, I want to search by name, SKU, brand, or keywords and refine results with filters and sorting, so that I can compare professional and residential lighting efficiently.

- **Given** the catalog contains at least 18 seeded SKUs with lighting attributes **when** I enter a search term matching a product name or SKU **then** matching products appear in the search results list with thumbnail, title, and unit price displayed in major units derived from integer pence
- **Given** I am viewing a product list **when** I apply filters for price range, brand, category, wattage, color/finish, and availability where the seed supports them **then** only products matching all selected filters are shown
- **Given** I am viewing a product list **when** I sort by price, newest, or popularity **then** the list order updates according to the selected sort (popularity per seeded merchandising weight or sales proxy defined in seed)

### US-003 View product detail, variants, and lighting specifications (must)
As a shopper, I want to see images, description, price, stock, variants, and relevant lighting specs on the product detail screen, so that I can buy the correct variant with confidence.

- **Given** a product has multiple variants (e.g. finish, wattage, color temperature) **when** I open product detail and select a variant **then** price, SKU, stock availability, and variant-specific attributes update for the selected variant
- **Given** a product is seeded with lighting attributes **when** I scroll the specifications section **then** I see only attributes relevant to that product type (e.g. wattage, lumens, color temperature, IP rating, dimmable, finish, dimensions, installation type) with values matching API/seed data
- **Given** Release 2 imagery is bundled under app/assets and/or API static paths **when** I view the product in list, detail, home carousel, or cart line item **then** at least one real product photo loads from bundled assets without relying on hotlinking alone (offline emulator demo works)

### US-004 Register, log in, log out, and merge guest cart (must)
As a shopper, I want to create an account, authenticate with JWT, and merge my guest cart on login, so that I do not lose items when I sign in before checkout.

- **Given** I am a guest with items in my session cart **when** I register a new account or log in with valid credentials **then** guest cart lines merge into my user cart (matching variant SKUs combine quantities per business rules) and persist for future sessions
- **Given** I am logged in **when** I log out **then** my session token is cleared on the client and subsequent cart operations require login for persistence or continue as guest per app policy without exposing another user's cart
- **Given** I submit registration with a weak or invalid password **when** the server validates input **then** I see a clear validation error and no account is created; passwords are stored hashed (bcrypt or argon2) on the server

### US-005 Manage shopping cart (must)
As a shopper (guest or signed-in), I want to add, update quantity, and remove line items and see accurate totals, so that I can review my order before checkout.

- **Given** a variant has sufficient stock **when** I add it to the cart from product detail or listing **then** the cart shows line item with product name, variant label, unit price in pence, quantity, line subtotal, and bundled product image thumbnail
- **Given** I change quantity on a cart line **when** the requested quantity exceeds available stock for that variant **then** the app prevents the update and shows an out-of-stock or max-quantity message without overselling
- **Given** my cart has items **when** I view cart totals **then** subtotal sums line prices using integer minor units; shipping and discount lines appear when applicable at checkout preview

### US-006 Save and manage wishlist (registered users only) (should)
As a signed-in customer, I want to add and remove products or variants from my wishlist synced via API, so that I can save favorites for later purchase.

- **Given** I am logged in **when** I tap save to wishlist on a product **then** the item is persisted via API and appears on my wishlist screen after refresh or navigation
- **Given** I am a guest **when** I attempt to use wishlist **then** I am prompted to register or log in; no local-only guest wishlist is offered in Release 2
- **Given** I have wishlist items **when** I remove an item **then** it is deleted via API and no longer appears in the list

### US-007 Complete UK checkout with contact and shipping (must)
As a shopper (guest or signed-in), I want to enter contact details and a UK shipping address and review my order before payment, so that I can receive delivery under simplified domestic rules.

- **Given** my cart subtotal is below the free-delivery threshold defined in seed/config **when** I proceed to checkout with a valid mainland UK address **then** standard flat-rate UK domestic shipping is applied and displayed in pence with copy stating standard domestic delivery only
- **Given** my cart subtotal meets or exceeds the free-delivery threshold (e.g. £75) **when** I review checkout **then** shipping cost is zero and the UI states free delivery applies
- **Given** I am on order review **when** I confirm line items, subtotal, shipping, optional coupon discount, and total **then** all amounts match server-calculated totals in GBP pence and VAT-inclusive B2C prices

### US-008 Pay with mock secure payment and place order (must)
As a shopper, I want to complete a clear payment step without entering raw card data on our servers, so that my order is placed and marked paid after successful mock confirmation.

- **Given** I have a valid checkout and stock is reserved for my cart variants **when** I submit mock payment successfully **then** the order is created in pending_payment, transitions to paid upon mock confirmation, stock reservation is consumed, and I see confirmation with a unique order number
- **Given** mock payment fails or is cancelled **when** the payment step completes unsuccessfully **then** the order is not marked paid, reserved stock is released, and I see a recoverable error with option to retry without creating duplicate paid orders for the same idempotent checkout attempt
- **Given** I am on the payment step **when** I interact with the UI **then** no full card PAN or CVV is transmitted to or stored on the application backend; demo copy explains secure payment pattern for future gateway swap

### US-009 Apply coupon code at checkout (must)
As a shopper (guest or signed-in), I want to enter a valid coupon code during checkout, so that I receive the seeded promotion discount on my order.

- **Given** a seeded coupon is active with no minimum or my subtotal meets the minimum order value **when** I enter the coupon code at checkout **then** exactly one coupon is applied to the order subtotal after line-item sale or variant prices are reflected, and discount and revised total display in pence
- **Given** I have already applied one coupon **when** I attempt to apply a second coupon **then** the app rejects stacking and shows that only one code per order is allowed
- **Given** a coupon is restricted to a category or SKU in seed data **when** my cart does not qualify **then** the server rejects the coupon with a clear message and totals remain unchanged

### US-010 Receive order confirmation (must)
As a shopper, I want to see an order confirmation screen after successful placement, so that I trust the purchase completed.

- **Given** mock payment succeeded **when** I land on confirmation **then** I see order number, summary of lines with snapshotted product names and unit prices, shipping address, totals, and estimated delivery copy for UK standard shipping
- **Given** order lines were persisted **when** catalog prices or product names change later **then** historical order detail still shows the name and unit price captured at purchase time

### US-011 View order history and tracking (must)
As a signed-in customer, I want to view my past orders and see status progression and shipment info, so that I know when my lighting order is processing, shipped, or delivered.

- **Given** I am logged in and have at least one order **when** I open order history **then** I see a list of orders with order number, date, total in GBP, and high-level status mapped from pending_payment, paid, fulfilled, delivered (and cancelled/refunded only if present in seed for demo)
- **Given** I open an order detail **when** the order has seeded shipment info **then** I see customer-facing statuses aligned to processing → shipped → delivered and any carrier or tracking reference provided by seed/API
- **Given** I am a guest who completed checkout **when** I attempt to view order history without an account **then** I am directed to register or log in; guest order lookup by email is out of scope unless explicitly seeded as demo-only copy pointing to support

### US-012 Reset password (Release 2 demo flow) (should)
As a registered customer, I want to request a password reset, so that I can recover access to my account.

- **Given** I enter a registered email on forgot password **when** I submit the request **then** I see a generic success message (e.g. check your email) without revealing whether the email exists
- **Given** Release 2 uses a stub provider **when** password reset is triggered **then** reset token or deep link behavior is logged or demo-documented; production email delivery is not required for Release 2 done

### US-013 Access customer support and FAQ (should)
As a shopper, I want an in-app support screen with UK contact details and FAQ link, so that I know how to get help with orders, delivery, and returns policy.

- **Given** I open customer support **when** the screen loads **then** I see business hours, phone, email, and a link or WebView to FAQ covering shipping, mock payment demo, and that returns/refunds are handled via support until a later release
- **Given** emergency or compliance-oriented products appear in catalog copy **when** I read product or FAQ text where seeded **then** disclaimers clarify demo catalog and direct buyers to specialist advice where appropriate

### US-014 Ship production-style catalog with documented imagery (must)
As a product owner / QA, I want 18–30 real lighting SKUs with bundled photos and documented sources aligned across Flutter, Prisma seed, and OpenAPI, so that the Release 2 demo credibly represents a UK lighting retailer offline and online.

- **Given** imagery is sourced primarily from https://stanpro2.folio3.site/search and linked product pages **when** assets are downloaded into app/assets/catalog/images/ and/or API static seed paths **then** docs/IMAGE_SOURCES.md records URL, SKU mapping, and demo/staging use provenance
- **Given** catalog.json, Prisma seed, and API mappers are updated **when** I browse the app against API and offline fallback **then** the same 18–30 SKUs appear with consistent names, pence prices, variants, stock per variant, and lighting attributes
- **Given** M3 delivery completes **when** CI runs flutter analyze, flutter test, and server unit/e2e tests for new endpoints **then** all are green and OpenAPI documents new operations (health and infrastructure docs excluded from operation count caps per program rules)

## Non-functional requirements
- NFR-01 Performance: Primary catalog and product detail screens render within 2 seconds on a mid-range Android emulator on Wi‑Fi against staging API; search and filter requests show loading states within 500 ms.
- NFR-02 Supported platforms: Android first for demo (Flutter 3.x); define minimum Android API level in project README for stakeholder sign-off; iOS compatibility maintained at code level but App Store submission out of scope.
- NFR-03 Security: HTTPS for all API calls in staging; JWT for authenticated endpoints; passwords hashed with bcrypt or argon2; no storage of raw card data; mock payment only in Release 2; rate-limit auth endpoints where feasible.
- NFR-04 Privacy and GDPR: Collect minimum personal data (account, shipping, order history); support account deletion API/app flow; privacy copy on registration; no production marketing push in this pass.
- NFR-05 Data integrity: All monetary values stored and transmitted as integer minor units (pence) with currency code GBP; prevent overselling via per-variant stock checks and reservation on checkout; idempotent order placement to avoid duplicate paid orders on double-submit.
- NFR-06 Availability and failure handling: Graceful degradation when API unavailable (Pass 1 local catalog fallback); clear errors for network, checkout, payment, and coupon validation failures; retry without data loss where safe.
- NFR-07 API contract: NestJS OpenAPI (/api/docs-json) stays in parity with implemented M3 endpoints; health check exposed; infrastructure routes excluded from M3 operation budget per program rules; maximum 28 API operations for Release 2 scope.
- NFR-08 Testing: flutter analyze and flutter test green; Jest unit and Supertest e2e coverage for new auth, cart, checkout, orders, coupons, wishlist, and home merchandising endpoints; one structured M3 QA round before Release 2 sign-off.
- NFR-09 Accessibility: Touch targets and semantic labels on primary flows (browse, cart, checkout); support system font scaling; target WCAG 2.1 AA as backlog unless audit scheduled in M3.
- NFR-10 Analytics: Instrument hooks for product view, add-to-cart, and purchase completion events (log or stub provider) for future optimization without blocking demo.
- NFR-11 Scalability: Stateless API suitable for horizontal scaling in staging; PostgreSQL 16 via Prisma; no single-server demo assumptions that block later production hardening.
- NFR-12 Release scope caps: At most 14 user stories, 14 work items (WI-013–WI-026), 1 milestone (M3), 14 app screens, and 28 API operations—trim features before exceeding caps.

## Out of scope
- Pass 1 replan or rework of WI-001 through WI-012 except small deltas required for Release 2 integration
- Full admin panel UI for AR-01–AR-09 (API-first admin and optional minimal UI or documented API only)
- Stripe PaymentIntents, webhooks, and production payment keys in Release 2 (follow-on for production readiness)
- Guest wishlist or local-only favorites
- Trade account types, ex-VAT display, trade pricing, and volume discount tiers
- Multiple UK shipping zones, carrier selection, weight-based shipping, surcharges for oversized/fragile SKUs, click-and-collect
- In-app customer cancel, return, refund, or warranty claim workflows (statuses may exist API-only for staff demo)
- Production push notifications and transactional email/SMS (FR-18 mock/log only)
- iOS App Store submission and production image licensing for public redistribution
- Multi-currency and Ireland/EU expansion
- Live ERP/WMS inventory sync beyond seeded quantities
- Production analytics platform and KPI dashboards beyond event hooks
- Apple Pay, Google Pay, trade credit, and non-mock payment methods

## Assumptions
- Working customer-facing name is Lumen until retail brand is finalized.
- All catalog, cart, and checkout prices are VAT-inclusive B2C GBP shown to all personas including trade buyers.
- Shipping uses one standard flat rate for mainland UK plus free delivery over a stated threshold (e.g. £75) documented in seed and checkout copy.
- Popularity sort uses a seed-defined merchandising weight or sales proxy documented in backend seed.
- Order lifecycle for shoppers displays processing → shipped → delivered mapped from paid → fulfilled → delivered backend states where applicable.
- Cancelled and refunded orders may appear in API/seed for staff but have no shopper-initiated actions in Release 2.
- Milestone M3 delivers new work items WI-013 upward only; example mapping includes auth (WI-013), cart merge (WI-014), checkout/shipping (WI-015), mock payment/orders (WI-016), coupons (WI-017), wishlist (WI-018), home merchandising (WI-019), order history/tracking (WI-020), catalog imagery/seed expansion (WI-021), OpenAPI/client sync (WI-022), support screen (WI-023), password reset stub (WI-024), analytics hooks (WI-025), M3 QA fixes (WI-026)—exact titles owned by engineering backlog.
- Demo imagery from stanpro2.folio3.site is for demo/staging until license review.
- Maximum 14 app screens cover: Home, Categories, Product List, Search Results, Product Detail, Cart, Checkout (address/review), Mock Payment, Order Confirmation, Login/Register, Account/Profile, Order History, Order Detail, Wishlist, Support (some screens may combine tabs to stay within cap).
- Account deletion is supported to meet UK GDPR expectations; retention policy details deferred to legal sign-off.
- Notifications for order confirmation and shipping are logged or mocked, not delivered via FCM/APNs in Release 2.
