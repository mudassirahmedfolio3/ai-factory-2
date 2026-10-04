# Lighting Retail Mobile App (MVP) — Product Requirements Document

Mobile-first lighting e-commerce for the United Kingdom (GBP, en-GB, domestic shipping only). This PRD defines a client-demo release in two milestones: M1 — a showable Flutter app on Android (API 26+) with guest shopping, 12–20 seeded lighting SKUs in local mock data, cohesive design system, product listing with search and filters, product detail with star ratings and reviews, lighting-specific specifications, and an in-memory cart with quantity updates; M2 — a NestJS /api/v1 slice with health check and catalog OpenAPI backed by stub/seed data matching the same products, with Dart API client integration when analyze/tests pass (M1 mock path remains if integration blocks the demo). Full MVP (post-demo) extends the same journey with registered accounts, guest checkout with Stripe PaymentIntents, order history, email notifications, coupons, wishlists, and admin catalog/order operations. Prices are integer minor units (pence) with ISO 4217 GBP; stock is per variant with reservation at checkout in production; order lifecycle pending_payment → paid → fulfilled → delivered plus cancelled/refunded when those features ship.

## Personas
### Guest Shopper (Demo Primary)
Residential customer browsing and buying without creating an account; primary persona for stakeholder demo sign-off on Android emulator.
- Discover lighting products by category, search, and filters
- Compare specifications (wattage, lumens, color temperature, IP rating) on product detail
- Build a cart and adjust quantities before a future checkout step
- Trust accurate availability and pricing shown in GBP

### Registered Customer
Homeowner or trade buyer who creates an account for order history, persisted wishlist, and password recovery (post-demo MVP).
- Register, sign in, and reset password securely
- Complete checkout with UK shipping and Stripe card payment
- View order history and track status with optional carrier tracking number
- Save favorites to a wishlist synced across devices

### Trade / Semi-Professional Buyer
Electrician, small contractor, or interior designer who needs spec-rich listings and filters (wattage, dimming, IP rating).
- Filter catalog by technical attributes relevant to installation
- Read full lighting specifications on product detail pages
- Identify in-stock variants quickly for job quoting

### Store Administrator
Internal operator with a single admin role managing catalog, inventory, orders, promotions, and homepage content (API or minimal UI; not in this demo run).
- Add, edit, and deactivate products without deleting historical records
- Manage variants, SKUs, prices, and stock quantities
- Update order status (processing, shipped, delivered) and optional tracking
- Configure coupons, banners, and featured products

## User stories
### US-001 Browse lighting catalog on home and product listing (must)
As a guest shopper, I want to open the app and browse a curated list of lighting products with images, names, prices, and availability, so that I can quickly find fixtures and accessories for my project without signing in.

- **Given** the app is installed and launched on Android API 26 or higher with 12–20 seeded products in local mock data **when** I land on the home or primary product listing screen **then** I see a client-ready UI (not the default Flutter counter template) showing product cards with image, name, price in GBP (pence stored as integer minor units, displayed formatted), and an Out of stock badge when applicable
- **Given** seed data includes products across the default taxonomy (Ceiling Lights, Wall Lights, Outdoor & Security, Bulbs & Tubes, LED Strips & Profiles, Lamps & Portable, Commercial & Trade) **when** I navigate from home into a category or subcategory browse path exposed in the demo (within the six-screen limit) **then** the listing filters to products in that category and remains scrollable with stable layout on emulator
- **Given** a product has a sale or list price **when** it appears on the listing **then** the displayed price reflects the catalog price in GBP minor units without floating-point rounding errors in stored values

### US-002 Search products by name, SKU, brand, and keywords (must)
As a guest shopper, I want to search the catalog by text, so that I can find a specific fixture or bulb quickly.

- **Given** I am on the product listing or search entry point included in the demo screens **when** I enter a query matching a product name (e.g. "Modern LED Ceiling Light") **then** the list shows matching products and hides non-matching items
- **Given** seed products include SKUs and brand attributes (e.g. SKU CL-1001) **when** I search by SKU or brand keyword **then** relevant products appear in results with no sign-in required
- **Given** I enter a query with no matches **when** search is applied **then** I see an empty state message and can clear search to restore the full list

### US-003 Filter and sort product listing (must)
As a guest shopper, I want to filter and sort products by price, brand, category, wattage, color/finish, and availability, so that I can narrow results to fixtures that meet my budget and technical needs.

- **Given** the listing shows multiple products with varied brands, categories, wattages, and stock states **when** I apply a price range filter in GBP **then** only products whose current variant or base price falls within the range remain visible
- **Given** filters for brand, category, wattage, color/finish, and availability are available on the listing screen **when** I select one or more filters **then** results update to match all active filters and I can reset filters to defaults
- **Given** sort options include price (low/high), newest, and popularity **when** I choose popularity sort **then** products order by manual merchandising popularity rank (lower number first), tie-breaking by units sold in the last 90 days where rank is equal or unset

### US-004 View product detail with lighting specs, variants, ratings, and reviews (must)
As a guest shopper, I want to open a product detail page with images, description, pricing, variants, lighting specifications, star ratings, and reviews, so that I can decide whether the product fits my room and installation requirements.

- **Given** I select a product from the listing **when** the product detail screen loads **then** I see product name, SKU, price in GBP, stock state, image gallery, and description appropriate to the product type
- **Given** the product is a lighting SKU with domain attributes **when** I view the specifications section **then** only relevant fields are shown among Product Name, SKU, Wattage, Lumens, Color Temperature, Light Type, Voltage, Dimmable, Material, Finish, Dimensions, IP Rating, Bulb Included, Installation Type (example: 24W, 2400 lm, 3000K, IP44, Dimmable Yes)
- **Given** the product has variants (e.g. finish, wattage, color temperature) and seeded star ratings and reviews **when** I change variant selection **then** price, SKU, availability, and add-to-cart enabled state update for the selected variant; out-of-stock variants disable add-to-cart; ratings summary and review list are visible on the detail page

### US-005 Manage an in-memory shopping cart (must)
As a guest shopper, I want to add products to a cart, change quantities, remove items, and see totals, so that I can review my selection before checkout in a later milestone.

- **Given** I am on product detail with an in-stock variant selected **when** I tap add to cart **then** the item appears in the cart with correct name, unit price snapshot for the session, variant label, and quantity one
- **Given** I have items in the in-memory cart **when** I increase or decrease quantity or remove a line **then** line totals and cart subtotal update immediately without requiring sign-in
- **Given** a variant is out of stock **when** I attempt to add it to cart from detail **then** add-to-cart is disabled or blocked with a clear message and the cart is unchanged

### US-006 Consume catalog from NestJS API (M2) (must)
As a guest shopper using the app configured for API mode, I want the app to load the same product catalog from the backend when available, so that the demo proves API contract alignment beyond local mocks.

- **Given** NestJS serves GET /api/v1/health returning healthy status and GET /api/v1/catalog (or equivalent catalog list/detail operations within the 12-operation budget) with seed data matching M1 products **when** the Flutter app is pointed at the running API and OpenAPI-generated client integration is enabled after analyze/tests pass **then** product listing and detail display the same SKU set and core fields (name, price minor units, currency GBP, availability, specs) as local mock data
- **Given** the API is unreachable or client generation/integration fails **when** I launch the app for the stakeholder demo **then** the M1 local mock data path still works and documentation notes API readiness for follow-up integration
- **Given** OpenAPI is published at /api/docs-json (infrastructure, not counted toward the 12 API operations limit) **when** a developer generates the Dart dio client **then** the catalog operations used by the app are described with request/response schemas including integer price minor units and ISO 4217 currency code GBP

### US-007 Registered account access and order history (full MVP) (should)
As a registered customer, I want to register, log in, log out, reset my password, and view past orders, so that I can manage my profile and track purchases over time.

- **Given** I am a new user on the full MVP build (post demo run) **when** I register with email and password and verify required fields **then** my password is stored hashed (bcrypt or argon2), I can log in and log out, and my cart belongs to my signed-in user session per domain rules
- **Given** I forgot my password **when** I complete the password reset flow **then** I can set a new password and sign in without support intervention under normal conditions
- **Given** I have placed paid orders on my account **when** I open order history **then** I see orders with lines copying product name and unit price at purchase time, statuses aligned to pending_payment → paid → fulfilled → delivered (plus cancelled/refunded when supported), and guest lookup remains order number plus email for non-account orders

### US-008 Checkout, UK shipping, VAT, Stripe payment, and order confirmation (full MVP) (should)
As a guest or registered customer on the full MVP, I want to complete checkout with contact details, UK shipping address, delivery option, coupon, tax review, and secure card payment, so that I receive an order number and email confirmation and the store fulfils without overselling.

- **Given** my cart has in-stock lines and I am at checkout review **when** I enter a valid UK domestic shipping address, choose Standard (3–5 business days, £4.99 flat or free over £75) or Express (1–2 business days, £9.99), and view totals **then** subtotal, single 20% VAT line on eligible goods, shipping, optional one coupon (pre-coupon subtotal of non-sale items only), and grand total in GBP minor units are shown before payment
- **Given** the server creates a Stripe PaymentIntent in test mode **when** I confirm payment with the Stripe SDK without card data touching our server **then** duplicate submission controls prevent double placement; on success I see order confirmation with order number; webhook marks order paid; stock was reserved at checkout and released on failed or expired payment
- **Given** payment fails or network drops mid-checkout **when** I retry or cancel **then** I see a clear error state, no duplicate paid orders occur, and reserved stock is released according to the single implemented inventory rule

## Non-functional requirements
- NFR-01 Performance: Product listing and detail screens load efficiently on Android emulator; catalog API list/detail responses suitable for demo without perceptible stall on seed catalog size (12–30 SKUs for demo; scalable to growth post-MVP).
- NFR-02 Compatibility: Minimum Android 8.0 (API 26) and iOS 15.0 for acceptance testing; MVP stakeholder sign-off requires runnable end-to-end guest shopper path on Android emulator at or above API 26; iOS build is phase 2 after Android sign-off.
- NFR-03 Security: HTTPS for all API traffic; JWT auth for registered users and admin on full MVP; bcrypt or argon2 password hashing; role-based access with single admin role for MVP; account deletion support on full MVP; no raw card data on our systems.
- NFR-04 Payments: Stripe PaymentIntents in test mode on full MVP; server creates intent, mobile confirms via Stripe SDK, webhook marks order paid; Apple Pay, Google Pay, wallets, and BNPL out of scope for MVP sign-off.
- NFR-05 Usability: Mobile-first layouts within at most six app screens for this demo run; intuitive navigation (home/listing, search/filter, detail, cart, and supporting flows consolidated as needed); single-brand retailer experience with multi-manufacturer brands as filters.
- NFR-06 Reliability: Graceful handling of network failures on catalog fetch with fallback to M1 mocks; checkout payment and duplicate-submission handling on full MVP; consistent stock reservation rule to prevent overselling.
- NFR-07 Scalability: NestJS + PostgreSQL 16 + Prisma architecture supports growth in products, customers, and orders beyond demo seed size.
- NFR-08 Accessibility: Readable text, sufficient contrast, and accessible controls (best-effort for demo; target WCAG 2.1 AA as goal for launch hardening).
- NFR-09 Data Integrity: Prices stored as integer minor units (pence) with currency GBP; order lines snapshot name and unit price at purchase; coupons respect one per order, expiration, optional minimum order value, single-use per email when configured, no stacking on sale lines; no overselling at order placement.
- NFR-10 Analytics: Track product views, cart adds, and purchases for MVP; product views do not drive popularity sort (manual rank primary, 90-day units sold tie-break).
- NFR-11 Privacy: Store minimum personal data; support account deletion on full MVP; email required for guest checkout and transactional email notifications on full MVP.
- NFR-12 Localization: United Kingdom only for MVP — en-GB language, GBP currency, domestic UK addresses validated; no cross-border shipping or multi-locale.
- NFR-13 Notifications: Email required for order confirmation and shipping/status updates on full MVP; push notifications not required for MVP sign-off.
- NFR-14 Tax and shipping: Single fixed 20% VAT on eligible goods at checkout review; Standard £4.99 (free over £75) and Express £9.99; no weight-based or carrier-calculated rates in MVP.
- NFR-15 Delivery engineering: Flutter 3.x with cohesive design system chosen without external style-approval gates; NestJS /api/v1 with OpenAPI; Docker/docker-compose for staging; health check endpoint included and excluded from API operation count cap.

## Out of scope
- This demo run: production payments, live Stripe checkout in the meeting build, Apple Pay, Google Pay, wallets, and buy-now-pay-later.
- This demo run: admin panel UI, marketing website, production email delivery (mock or log narrative acceptable for demo).
- This demo run: sign-in required for demo meeting — guest shopping only on M1; account flows documented in US-007/US-008 for full MVP.
- This demo run: more than eight user stories, twelve work items, two milestones, twelve API operations, or six app screens; infrastructure /health and /api/docs-json excluded from API operation cap.
- Full MVP deferred from demo run: in-app return requests and admin refund workflow updating order status to refunded (display-only returns policy text instead).
- Live carrier API tracking integration (manual admin status plus optional carrier name and tracking number only).
- Push notifications for order and shipping updates.
- Cross-border shipping, multiple locales, jurisdiction-based tax (fixed 20% VAT only).
- Guest persisted cart on server without account (cart belongs to signed-in user on full MVP; demo uses in-memory cart).
- Separate admin roles (catalog vs orders vs super-admin).
- International markets beyond UK domestic.
- iOS build and simulator testing as gate for MVP demo sign-off (phase 2 after Android).
- Work items requiring human approval, stakeholder sign-off, or style-approval gates.

## Assumptions
- Default category taxonomy is fixed for build: Ceiling Lights (flush & semi-flush, pendant, chandelier, track & spot); Wall Lights (sconces, picture lights, bathroom vanity); Outdoor & Security (wall lanterns, flood & security, garden & path, porch); Bulbs & Tubes (LED bulbs, smart bulbs, tubes & capsules); LED Strips & Profiles (strips, drivers, profiles & accessories); Lamps & Portable (desk, floor, table); Commercial & Trade (panel, high-bay, emergency); merchandising may refine labels before launch without structural change.
- Seed catalog contains 12–20 products for demo mock assets and matching backend seed (15–30 SKUs acceptable for full MVP seed); stock placeholders and representative images acceptable for MVP photography.
- Popularity sort uses admin-set merchandising rank first, then 90-day units sold; view counts tracked but not used for sort in MVP.
- Guest wishlist may exist device-local for demo; persisted cross-device wishlist requires registered account on full MVP.
- Customer support for MVP is in-app business hours, phone, email, and FAQ link; no live chat bot.
- Returns and refunds policy is linked from checkout, confirmation, and support; customers contact phone or email for returns.
- Legal copy for terms of service, privacy policy, and consent to be provided by business stakeholders before public launch; demo may use placeholder legal links.
- Stripe test mode is the payment gateway for full MVP card payments only.
- Order tracking on full MVP maps customer-visible statuses to processing, shipped, and delivered with manual admin updates.
- Single admin role has full AR-01–AR-09 capabilities via API or minimal admin UI after demo run.
- M2 integration: Dart OpenAPI client generated only when analyze/tests pass; otherwise M1 mock path is the demo fallback with documented API readiness.
