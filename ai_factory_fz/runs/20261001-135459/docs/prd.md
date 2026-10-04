# Product Requirements Document: Simple Ecommerce App (M1 Speed Demo MVP)

Create a simple ecommerce app that lets customers browse products, add items to a cart, and complete purchases on mobile, so a growing retail business can sell online with a clear, easy shopping experience. For this first milestone (SPEED DEMO), deliver the smallest runnable Flutter MVP only: a mobile-first product catalog with browse (product list) and product detail screens, backed by a local/mock catalog so the app runs on an emulator immediately. An optional in-memory shopping cart may be included. Auth, payments, checkout, order fulfillment, and backend API work are deferred. Catalog target for the broader product: roughly 50–150 products across Apparel, Accessories, Home, and Essentials (or equivalent); English; single currency (USD unless store local currency is set). Prices are integer minor units (cents) with ISO 4217 currency code. Tax-inclusive display. Later releases will add guest checkout, signed-in accounts, Stripe PaymentIntents, local delivery and in-store pickup, and order status tracking.

## Personas
### Everyday Shopper
A mobile shopper who wants a quick, clear way to browse and understand products before buying. In M1 they explore the catalog and product details; purchase flow comes in a later release.
- Browse products quickly on a phone
- See clear names, prices, images, and descriptions
- Find items via search or simple category filters
- Understand availability before deciding to buy

### Returning Customer
A shopper who expects a familiar browsing experience and, in later releases, saved preferences and order history. For M1 they need a reliable catalog and product detail experience.
- Revisit products easily
- See consistent pricing and product information
- Prepare to purchase once checkout is available

### Retail Owner / Staff
Business operators who need a simple foundation for selling online without heavy technical complexity. M1 validates that customers can discover products on mobile before checkout and ops tooling are added.
- Offer a clear mobile product catalog
- Validate that shoppers can find and understand products
- Ship a lean first release that can grow into cart, checkout, and order management

## User stories
### US-001 Browse product catalog (must)
As a everyday shopper, I want to see a list of products with name, price, image, and basic availability on a mobile product list screen, so that I can quickly discover what the store sells without creating an account or connecting to a live backend.

- **Given** the Flutter app is launched on an Android emulator with a local/mock catalog of products across a small set of retail categories (e.g. Apparel, Accessories, Home, Essentials) **when** I open the product list (browse) screen **then** I see product cards showing name, tax-inclusive price displayed from integer minor units with an ISO 4217 currency code (e.g. USD cents), a product image (or placeholder), and an indication when a product is out of stock
- **Given** the mock catalog contains products in more than one category **when** I apply a simple category filter or enter a search term that matches a product name **then** the list updates to show only matching products and I can clear the filter/search to return to the full list
- **Given** the mock catalog is empty or fails to load **when** I open the product list screen **then** I see an empty or error state with a clear message and no crash

### US-002 View product detail (must)
As a everyday shopper, I want to open a product detail screen from the list, so that I can read the full description, confirm price and availability, and decide whether I want the item.

- **Given** I am on the product list screen and at least one in-stock product is visible **when** I tap that product **then** I navigate to a product detail screen showing name, tax-inclusive price (integer minor units + currency code), image, basic description, category, and stock/availability for the product (or its default variant)
- **Given** I am viewing an out-of-stock product on the detail screen **when** the screen finishes loading **then** availability is clearly shown as unavailable/out of stock and any add-to-cart action (if present) is disabled or blocked with a clear message
- **Given** I am on the product detail screen **when** I use the back/navigation control **then** I return to the product list without losing my previous list filter or search state if one was applied

### US-003 Add items to an in-memory cart (must)
As a everyday shopper, I want to add a product from the detail screen to a simple in-memory cart and update or remove quantities, so that I can try a basic cart flow in the demo without accounts, payments, or a backend.

- **Given** I am on a product detail screen for an in-stock product and the cart is empty **when** I add the product to the cart with a valid quantity **then** the in-memory cart contains that line with product name, unit price snapshot in integer minor units with currency code, and quantity, and a cart indicator or cart screen reflects the updated count
- **Given** the in-memory cart already contains a product line **when** I increase, decrease, or remove the quantity from the cart UI **then** the cart updates immediately in memory, quantity never goes below 1 unless the line is removed, and I cannot add more units than available mock stock for that product/variant
- **Given** I have items in the in-memory cart **when** I fully restart the app process **then** the cart is empty again (session-only; no persistence, auth, checkout, or payment in M1)

## Non-functional requirements
- Mobile-first Flutter 3.x Android app must launch on an emulator with a local/mock catalog and no mandatory backend for M1.
- Product list should become interactive within a few seconds of cold start on a typical emulator using mock data.
- Prices must be represented and displayed from integer minor units (cents) with an ISO 4217 currency code; never floating-point money values.
- Stock awareness is per product (or default variant) in mock data so out-of-stock items cannot be added to the in-memory cart.
- UI must remain usable on common phone widths; text contrast and tap targets should meet basic mobile accessibility expectations for list and detail screens.
- No collection of personal data, passwords, or payment details in M1; card data never touches any app server (deferred with Stripe PaymentIntents to a later release).
- Scope caps for this run: at most 3 user stories, 3 app screens (product list, product detail, optional cart), 1 milestone, and no live commerce API work required for M1.
- English language and a single primary currency (USD unless otherwise configured) for the launch market; tax-inclusive price display.

## Out of scope
- Guest checkout, account registration, login, JWT auth, and saved preferences or order history
- Stripe PaymentIntents, digital wallets, cash on delivery, and any payment confirmation or webhooks
- Checkout, delivery address capture, local delivery, in-store pickup, and shipping
- Order creation, order status (pending_payment, paid, fulfilled, delivered, cancelled, refunded), confirmations, and refunds
- Backend NestJS API, Prisma/PostgreSQL catalog, and remote OpenAPI-driven client work for M1 (prefer local mock catalog)
- Multi-vendor marketplace, advanced personalization, multi-language, and multi-currency
- Admin/catalog management tooling for retail staff
- Return request workflow beyond displaying a simple return policy note if shown in UI later
- Persistent cart across restarts, guest or signed-in cart sync, and inventory reservation at checkout
- Any work items requiring human approval, stakeholder sign-off, or style approval

## Assumptions
- M1 is a SPEED DEMO: start coding immediately with Flutter screens and mock catalog data; style tokens may be chosen by the agent without waiting.
- Guest checkout, optional accounts, Stripe cards, local delivery + in-store pickup, 14-day return policy (refund to original payment method), and tax-inclusive pricing remain product intent for later milestones but are not built in M1.
- Catalog size for the broader product is approximately 50–150 products; the M1 mock catalog may be a smaller representative set across Apparel, Accessories, Home, and Essentials (or equivalent).
- Single market initially: English and one primary currency (USD unless the store’s local currency is already set).
- A cart in M1 is optional, in-memory only, and does not require a signed-in user; project default of signed-in carts applies when checkout/auth are introduced later, with guest checkout explicitly required at that launch.
- Infrastructure health endpoints are out of M1 app scope; no backend API operations are required to demonstrate browse and detail.
