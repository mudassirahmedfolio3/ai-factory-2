# SoftAura Skin Care Flutter E-Commerce MVP — M1 Speed Demo PRD

SoftAura is a Flutter Android-first skincare storefront for busy adults shopping everyday body and face care (curated third-party brands in the Olay Ultra Moisture Shea Butter Body Wash ~$12.99 style). This M1 SPEED DEMO delivers the smallest runnable Flutter MVP with a local/mock catalog of 24 SKUs across Body Wash, Cleansers, Moisturizers, and Face Care so the app runs on an emulator immediately. Must-have screens: product list (browse) and product detail. Optional: simple in-memory cart. SoftAura visual identity: clean, calm UI with soft sage green (#7A9E8E) primary accent, warm ivory backgrounds, charcoal text, and rounded product imagery. Auth, payments, checkout, backend API, order history, promo codes, reviews, wishlist, and shipping are deferred after this sprint increment.

## Personas
### Everyday Skincare Shopper
Busy adult browsing SoftAura on Android for trusted everyday body and face care (cleansers, body wash, moisturizers) from curated third-party brands, wanting a calm mobile-first experience to discover products quickly without creating an account in this demo.
- Browse a focused Skin Care catalog by category and product name
- Open a product detail page to see price, description, and imagery
- Optionally add items to a simple in-memory cart to preview a shopping basket

## User stories
### US-001 Browse SoftAura product catalog (must)
As a everyday skincare shopper, I want to see a scrollable list of SoftAura Skin Care products from a local mock catalog, so that I can discover body and face care items on my phone without waiting for a backend.

- **Given** the SoftAura Flutter app is launched on an Android emulator with the seeded mock catalog of 24 SKUs across Body Wash, Cleansers, Moisturizers, and Face Care **when** I open the product list (browse) screen **then** I see product cards showing at least product name, price displayed from integer minor units (cents) with ISO 4217 currency code USD (e.g. 1299 cents as $12.99), and rounded product imagery on a warm ivory background with sage green (#7A9E8E) accent and charcoal text
- **Given** the product list screen is displayed with the mock catalog loaded **when** I scroll the list **then** all seeded products remain reachable and the list does not crash or show empty placeholders for valid catalog entries
- **Given** the mock catalog includes products in multiple categories **when** I view the browse screen **then** each listed product is associated with one of Body Wash, Cleansers, Moisturizers, or Face Care so a QA engineer can verify category membership against seed data

### US-002 View product detail (must)
As a everyday skincare shopper, I want to open a product detail screen from the browse list, so that I can read name, price, description, and see imagery before deciding to buy later.

- **Given** I am on the SoftAura product list screen with at least one product visible **when** I tap a product card **then** I navigate to the product detail screen for that product and see name, price from integer cents with USD, category, description, and rounded product image using SoftAura styling (sage #7A9E8E accent, warm ivory, charcoal text)
- **Given** I am on a product detail screen **when** I use the back/navigation control **then** I return to the product list screen with the catalog still visible
- **Given** a product in the mock catalog has unit price 1299 cents USD (e.g. Olay Ultra Moisture Shea Butter Body Wash style listing) **when** I open that product’s detail screen **then** the displayed price equals $12.99 and is not rendered from a floating-point money value

### US-003 Optional in-memory cart (could)
As a everyday skincare shopper, I want to add a product from detail into a simple in-memory cart, so that I can preview selected items in this demo without auth or checkout.

- **Given** I am on a product detail screen and the optional in-memory cart is implemented **when** I tap Add to cart **then** the product is added to an in-memory cart (session only) and I can see the cart contains that product with name and unit price copied at add time
- **Given** the in-memory cart already contains one or more items **when** I leave the cart screen and return, or navigate between list and detail within the same app session **then** cart contents remain until the app process is killed; no persistence, auth, payment, or backend sync is required

## Non-functional requirements
- Android-first Flutter 3.x app; MVP must launch and run on an Android emulator without a live backend API for catalog data.
- Product catalog for M1 is local/mock seed data (24 SKUs, 4 categories); prices stored and handled as integer minor units (cents) with ISO 4217 currency code USD—never floats.
- SoftAura visual tokens may be chosen by the implementer without stakeholder style approval: primary accent #7A9E8E, warm ivory backgrounds, charcoal text, rounded product imagery; calm and trustworthy, not clinical or luxury-heavy.
- At most 3 app screens in M1 (product list, product detail, optional cart). At most 1 milestone. Prefer starting coding in the first build items.
- If any API surface exists in M1, at most 4 business API operations; infrastructure endpoints /health and /api/docs-json do not count toward that limit and health check must be included in the contract when a backend stub exists—otherwise no backend work if it slows delivery.
- Performance: product list and detail should become interactive within a few seconds of cold start on a standard emulator using local mock data.
- Accessibility: text contrast sufficient for charcoal on ivory; tappable targets large enough for mobile; screen navigation usable with standard Android back behavior.
- Privacy/security for M1: no account, no passwords, no card data, no PII collection required; do not send catalog or cart data to external payment providers in this increment.
- Testing: flutter_test coverage for price formatting (cents → display) and navigation from list to detail; optional widget/integration smoke test that the app starts and shows the browse screen.

## Out of scope
- User authentication, registration, JWT sessions, and guest vs signed-in carts
- Stripe PaymentIntents, payments, checkout, tax calculation, and order fulfilment
- Order history, order status flow, returns/refunds initiation, and email receipts
- Promo codes (WELCOME10, SAVE5) and stacking rules
- Product reviews, star ratings, and verified-buyer review gating
- Wishlist/favorites
- Push notifications
- Backend NestJS/Prisma/PostgreSQL catalog API work if it delays the Flutter emulator demo
- International shipping; contiguous US shipping rates and free-shipping threshold enforcement
- Account deletion and password hashing (no accounts in M1)
- iOS release as a primary delivery target for this sprint
- Human approval, stakeholder sign-off, or style-approval work items

## Assumptions
- Brand name SoftAura and visual identity tokens (#7A9E8E sage, warm ivory, charcoal, rounded imagery) are fixed for implementation without further brand approval gates.
- M1 catalog is curated third-party everyday skincare seed data: 24 SKUs across Body Wash, Cleansers, Moisturizers, and Face Care, including listings in the ~$12.99 body wash style.
- Scope-for-this-run SPEED DEMO rules override fuller SoftAura PRD ambitions: max 3 user stories, max 5 work items, max 1 milestone, max 4 API operations, max 3 app screens.
- In-memory cart is optional; product list and product detail alone satisfy the M1 must-have demo journey.
- Later releases may add signed-in carts, Stripe test-mode payments, promo codes, verified-buyer reviews, wishlist, order history, US flat $5.99 shipping / free over $35, and the 30-day unused-unopened return policy—none of which block M1.
- Currency for seeded prices is USD; all money values use integer cents.
