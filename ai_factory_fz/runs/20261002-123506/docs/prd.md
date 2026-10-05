# Womens Jewellery — Flutter MVP Product Requirements (M1 Speed Demo)

One-sprint Flutter MVP for the Womens Jewellery vertical that ships a demo-ready mobile shopping experience on Android (and iOS-capable Flutter) using a local/mock catalog. M1 delivers three screens only: product list (browse with search and filters), product detail (including mock reviews and star ratings), and a simple in-memory cart with quantity updates. Prices are integer minor units (cents) with ISO 4217 currency codes (e.g. Tropical Earring at 1999 USD cents). No auth, payments, checkout, order confirmation email, or backend API work in this milestone so the app runs immediately on an emulator. Stripe card checkout, account flows, confirmation email from orders@womensjewellery.demo, and verified-purchase reviews are deferred past M1.

## Personas
### Mobile fashion jewellery shopper
Woman browsing fashion and everyday jewellery on her phone, comparing accessible-priced pieces (around $20) by style, metal, and occasion before deciding what she likes.
- Browse a curated Womens Jewellery catalog quickly on mobile
- Filter by price, category, metal, and occasion
- Open a product and see price, details, star rating, and reviews
- Add items to a cart and adjust quantities during the demo journey

### Gift buyer
Shopper looking for an accessible gift such as earrings near the Tropical Earring ($19.99) price point, using ratings and filters to pick a suitable piece.
- Find gift-friendly pieces via occasion and category filters
- Trust the choice via visible star ratings and reviews on product detail
- Confirm selection by adding to cart with the right quantity

### Demo stakeholder
Internal stakeholder validating demand for the Womens Jewellery vertical with a small releasable Flutter increment that runs without backend setup.
- Launch a demo-ready app in one sprint
- Show browse → detail → cart without auth or payment blockers
- Keep scope to mock data so the emulator path is immediate

## User stories
### US-001 Browse jewellery catalog with search and filters (must)
As a mobile fashion jewellery shopper, I want to browse a local mock product list, search by text, and filter by price range, category, metal, and occasion, so that I can quickly find pieces that match my style and budget in the Womens Jewellery demo.

- **Given** the Flutter app is launched with a seeded local mock catalog that includes Tropical Earring priced at 1999 USD cents and other jewellery SKUs **when** I open the product list (browse) screen **then** I see a scrollable list of products each showing name, primary image or placeholder, and price formatted from integer cents with currency code (e.g. $19.99)
- **Given** I am on the product list screen with the mock catalog loaded **when** I enter a search query that matches a product name (e.g. "Tropical") **then** only products whose name or searchable text contains the query (case-insensitive) remain visible, and clearing search restores the full filtered set
- **Given** I am on the product list screen **when** I apply one or more filters among price range, category (earrings, necklaces, bracelets, rings), metal (gold-tone, silver-tone, rose gold), and occasion (everyday, work, gift, party) **then** the list shows only products matching all selected filters, and I can clear filters to return to the unfiltered (or search-only) list
- **Given** no products match the current search and filter combination **when** the filtered result set is empty **then** the screen shows an empty state message and does not crash or show stale items

### US-002 View product detail with reviews and star ratings (must)
As a gift buyer, I want to open a product and see its details, price, average star rating, and reviews from mock data, so that I can evaluate a piece before adding it to my cart in the demo.

- **Given** I am on the product list and Tropical Earring (or any listed SKU) is visible **when** I tap the product **then** I navigate to the product detail screen showing name, description, price from integer cents with currency, category, metal, occasion, and stock/availability display from mock data
- **Given** the selected product has mock review data with star ratings **when** I view the product detail screen **then** I see an aggregate star rating (1–5 scale) and a list of reviews each with star rating and review text; if a product has no reviews, an empty reviews state is shown
- **Given** I am on the product detail screen **when** I use the system or in-app back navigation **then** I return to the product list with prior search/filter state preserved for the demo session

### US-003 Manage in-memory shopping cart with quantity updates (must)
As a mobile fashion jewellery shopper, I want to add products to a simple in-memory cart and update quantities, so that I can complete a browse-to-cart demo journey without auth or checkout.

- **Given** I am on a product detail screen for an in-stock mock product **when** I choose Add to cart **then** the product is added to the in-memory cart with quantity 1 (or incremented if already present) and I can open the cart screen to see line items with name, unit price in cents/currency, and quantity
- **Given** my in-memory cart contains at least one line item **when** I increase or decrease the quantity for a line (decrease to 0 removes the line) **then** the cart updates immediately, line and cart totals recalculate using integer minor units only (no floating-point money math), and quantities never go below 0
- **Given** the app process is restarted **when** I open the cart again after a cold start **then** the in-memory cart is empty (persistence across restarts is not required for M1)

## Non-functional requirements
- Platforms: Flutter 3.x mobile app for Android first; iOS build supported by Flutter toolchain but demo verification focuses on Android emulator/device. Desktop web is out of scope.
- Performance: Product list with the seeded mock catalog (target ~12–20 SKUs) renders initial content within 2 seconds on a mid-range Android emulator after app start.
- Money handling: All prices stored and computed as integer minor units (cents) with an ISO 4217 currency code (USD for demo); never use floats for money.
- Privacy: M1 stores no personal accounts or payment data; no passwords; no PII collection beyond what the device already provides for running the app.
- Security: No auth or payment card data in M1; when payments are added later, card data must never touch our servers (Stripe PaymentIntents + SDK pattern).
- Accessibility: Interactive controls have visible labels; text contrast meets WCAG AA where feasible; tap targets are at least 44x44 dp for primary actions (Add to cart, filters, quantity steppers).
- Reliability: App must launch and complete browse → detail → cart flows offline using local mock data with no backend dependency.
- UX: Mobile-first layout; style tokens may be chosen by the implementation agent without stakeholder style approval.

## Out of scope
- User authentication, registration, JWT sessions, and account deletion
- Guest vs signed-in cart ownership rules (M1 cart is anonymous in-memory only)
- Stripe PaymentIntents, Apple Pay, Google Pay, cash-on-delivery, and any payment confirmation
- Checkout, order creation, order status flow (pending_payment → paid → fulfilled → delivered / cancelled / refunded)
- Order confirmation email (Womens Jewellery / orders@womensjewellery.demo deferred)
- Backend NestJS API, Prisma, PostgreSQL, OpenAPI client generation for shopping endpoints in M1
- Verified-purchase-only reviews; submitting new reviews from the app in M1 (display mock reviews only)
- In-stock-only filter; real inventory reservation/release
- Returns/refunds processing (placeholder policy copy deferred until checkout exists)
- Desktop or web storefront
- Push notifications, wishlist, recommendations, social login
- Human approval, stakeholder sign-off, or style-approval gates as work items

## Assumptions
- M1 is a SPEED DEMO: local/mock catalog inside the Flutter app; no backend API work that blocks emulator launch.
- Hard scope caps apply: at most 3 user stories, 3 app screens (list, detail, cart), 1 milestone, at most 4 shopping API operations later (none required for M1 shopping), infrastructure /health and /api/docs-json do not count when a contract appears.
- Starter catalog is agent-seeded (~12–20 SKUs) including Tropical Earring at 1999 USD cents as the reference listing.
- MVP filter dimensions beyond text search: price range, category, metal, occasion; in-stock-only is not required.
- Reviews and star ratings shown on detail come from mock data; any signed-in user may leave reviews in a later release—not in M1 write path.
- Stripe card-only checkout is the intended post-M1 payment method; Apple Pay/Google Pay are not required for the first paid demo.
- Post-M1 order confirmation email will use brand display name Womens Jewellery and from address orders@womensjewellery.demo.
- Post-M1 checkout will show the agreed short returns policy copy including support@womensjewellery.demo and earrings final-sale hygiene rule.
- Cart quantity updates are in-memory only for M1; stock reservation at checkout is deferred until payments exist.
- Domain e-commerce rules (cents pricing, order line price snapshots, Stripe webhook paid marking, bcrypt/argon2 passwords) apply to future milestones, not M1 implementation.
