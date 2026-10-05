# ShopEasy Mobile App - M1 Speed Demo PRD (Browse, Product Detail, In-Memory Cart)

Smallest runnable Flutter MVP of the ShopEasy mobile app, for a single milestone (M1) that runs on an Android emulator immediately. It has three screens: product list (browse), product detail, and an optional simple in-memory cart. The catalogue is a local mock bundled in the app, with no backend API work. Prices are stored as integer minor units (pence) with the ISO 4217 code GBP and displayed VAT-inclusive in English. There is no authentication, payments, checkout, or order management in this run. Those remain part of the wider MVP roadmap (sign-in, cart, Stripe test-mode payment, order tracking) and are deferred. Scope limits for this run: at most 3 user stories, 5 work items, 1 milestone, 4 API operations (0 needed, since the catalogue is local), and 3 app screens. Style tokens (colours, typography, spacing) are chosen by the build agent without waiting for any approval.

## Personas
### Shopper (browsing customer)
UK customer aged 18-55 who prefers shopping on their phone and wants to quickly look through the product range and see product details. In this demo they are not signed in.
- See the product range at a glance and open a product quickly
- View clear product details including price, description and available sizes/variants
- Collect items in a simple cart to see what they would buy

### Product team reviewer (demo audience)
Internal business stakeholder or developer who runs the demo app on an Android emulator to see the core shopping journey working. This is a demo audience only; no approval or sign-off step is part of this work.
- Launch the app on an emulator with no backend setup
- See the browse, detail and cart flow working end to end with mock data

## User stories
### US-001 Browse product list (must)
As a Shopper, I want to see a scrollable list of products with image, name and price on the home screen, so that I can quickly find something I like and open it.

- **Given** the app is installed on an Android emulator with no network backend available **when** the app is launched **then** the product list screen is shown within 3 seconds, populated from the local mock catalogue, with at least 8 products each showing an image (or placeholder), name and price
- **Given** a product in the mock catalogue has a unit price stored as an integer of 1999 with currency code GBP **when** it is shown in the product list **then** the price is displayed as £19.99 (VAT-inclusive), formatted from minor units with no floating-point arithmetic
- **Given** the product list screen is displayed **when** the shopper taps a product card **then** the product detail screen for that product opens
- **Given** the product list contains more items than fit on the screen **when** the shopper scrolls vertically **then** the list scrolls smoothly and all products can be reached

### US-002 View product detail (must)
As a Shopper, I want to open a product and see its photo, full name, description, price, variants (such as sizes) and stock status, so that I can decide whether to buy it.

- **Given** the shopper has tapped a product in the list **when** the product detail screen opens **then** it shows the product image, name, description, VAT-inclusive price in GBP, the available variants (for example sizes) and a stock status of in stock, low stock or out of stock
- **Given** the product detail screen is displayed **when** the shopper taps the back control or uses the system back gesture **then** the shopper returns to the product list at the same scroll position
- **Given** a variant in the mock catalogue has a stock of 0 **when** the product detail screen is displayed **then** that variant is shown as out of stock and cannot be selected or added to the cart
- **Given** a product has multiple variants **when** the shopper selects a variant **then** the selected variant is visibly highlighted and its stock status is shown

### US-003 Simple in-memory cart (could)
As a Shopper, I want to add a selected product variant to a cart and view the cart with quantities and a total, so that I can see what I would be buying.

- **Given** the shopper is on the product detail screen with an in-stock variant selected **when** the shopper taps Add to cart **then** the item is added to the in-memory cart with quantity 1 and the cart item count indicator increases by 1
- **Given** the cart contains items **when** the shopper opens the cart screen **then** each line shows product name, variant, unit price and quantity, and a total in GBP calculated from integer minor units is displayed (for example two items at 1999 and 500 pence show £24.99)
- **Given** the cart contains a line item **when** the shopper increases or decreases its quantity, or removes it **then** the line and the total update immediately, quantity cannot go below 1 (use remove instead), and quantity cannot exceed the variant's available mock stock
- **Given** the cart is empty **when** the shopper opens the cart screen **then** an empty-state message is shown and no checkout or payment control is displayed
- **Given** items are in the cart **when** the app is closed and relaunched **then** the cart is empty, because the cart is held in memory only for this demo

## Non-functional requirements
- Platforms: Flutter 3.x (Dart) single codebase; Android first and must run on an Android emulator with no backend setup; iOS build is not required for this run.
- Performance: the product list renders within 3 seconds of launch on a mid-range device or emulator; scrolling and screen transitions remain smooth with no visible jank; images load lazily and are sized for mobile.
- Data and money: all prices are integer minor units (pence) with ISO 4217 currency code GBP, never floats; displayed VAT-inclusive; English only.
- Mock data: the catalogue is a local in-app mock (minimum 8 products, each with at least one variant and a stock value) so the app works offline; no network calls are required.
- Security and privacy: no authentication, no personal data is collected or stored, no tracking or analytics, and no payment or card data is handled in this run.
- Accessibility: text is readable (minimum 14sp body text, sufficient colour contrast), tap targets are at least 48x48dp, and images and controls have semantic labels for screen readers.
- Styling: the agent chooses style tokens (colours, typography, spacing) itself in a single theme definition; no style approval step is required.
- Quality: the project builds and launches cleanly, and includes flutter_test widget tests for the list, detail and cart flows where they do not slow delivery.
- Contract note: M1 needs 0 API operations because the catalogue is local; if a backend is added later, a /health endpoint must be included in the contract and does not count toward the API operation limit.

## Out of scope
- User accounts, sign-up, sign-in (email, Apple, Google, phone) and password reset
- Guest checkout and saved addresses
- Payments, Stripe integration, Apple Pay, Google Pay, promo codes and gift cards
- Checkout, orders, order status flow, order history, tracking and returns or refunds
- Backend API, database, Stripe webhooks and real stock reservation (mock data only in M1)
- Stock sync with the inventory or ERP system
- Wishlist, customer reviews, loyalty points, personalized offers and live chat
- Push notifications (order updates, marketing, abandoned cart, back-in-stock)
- Search, filters, sorting and categories
- Delivery options, shipping cost calculation, VAT receipt emails and multi-region tax
- Admin back office and sales reports
- Multiple currencies, multiple languages and non-UK markets
- Persistent cart storage and iOS release, plus app store submission

## Assumptions
- The scope of this run takes priority over the wider brief and the clarified MVP roadmap; features listed as out of scope are deferred, not cancelled.
- One milestone (M1) is planned with at most 5 work items, and coding starts in the first work item.
- The catalogue is a local mock bundled with the app, so no backend or network setup is needed to run the demo.
- Market is the United Kingdom only, with GBP as the sole currency, English only, and prices shown VAT-inclusive at the standard 20% rate.
- The cart is an optional in-memory cart (US-003, priority could) and is the first thing to cut if delivery is at risk.
- Mock product images may be placeholders or bundled assets.
- Style tokens are chosen by the build agent with no stakeholder sign-off, and no work item requires human approval.
