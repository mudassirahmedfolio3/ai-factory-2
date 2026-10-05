# PRD: Comprehensive E-commerce App — Milestone 1 (Browse MVP)

Milestone 1 delivers the smallest runnable Flutter shopping experience for Android: a local/mock product catalog, a product list (browse) screen, a product detail screen, and an optional in-memory cart. Shoppers can discover products and inspect price, photos, description, variants, and availability without sign-in, payments, checkout, or a live backend. Prices are shown from integer minor units (cents) with ISO 4217 currency USD. This release proves the core browse journey on an emulator immediately; full checkout, guest checkout, accounts, Stripe, fulfillment, wishlist, push notifications, and admin ops are deferred to later milestones.

## Personas
### Mobile Browser Shopper
A busy shopper evaluating the brand on a phone who wants to scan the catalog quickly and open product details before deciding to buy later.
- Browse products without creating an account
- See clear prices, photos, and availability
- Open a product detail page in a few taps

### Returning Catalog Explorer
An existing or new customer discovering products who needs trustworthy product information (name, price, variants, stock) before purchasing in a future release.
- Find products in a simple list or catalog view
- Compare variants and stock on the detail screen
- Optionally add items to an in-memory cart for a preview of later checkout

## User stories
### US-001 Browse local product catalog (must)
As a mobile shopper, I want to open the app and see a list of products from a local/mock catalog, so that I can discover what is available without signing in or waiting on a backend.

- **Given** the Flutter app is launched on an Android emulator with the local/mock catalog loaded **when** I land on the product list (browse) screen **then** I see at least one product row showing product name, price formatted from integer cents in USD, and a primary image or placeholder
- **Given** the local/mock catalog contains multiple products with stock tracked per variant **when** I view the product list **then** each product shows enough information to identify it and I can scroll the list without a network call to a real API
- **Given** I am not signed in **when** I open the browse screen **then** the catalog is still fully visible and no auth gate blocks browsing

### US-002 View product detail (must)
As a mobile shopper, I want to open a product from the list and see its detail page, so that I can review photos, description, price, variants, and availability before deciding to buy later.

- **Given** I am on the product list with a visible product **when** I tap that product **then** I navigate to the product detail screen for that product
- **Given** I am on the product detail screen **when** the screen finishes loading from the local/mock catalog **then** I see product name, description, price in USD from integer cents (not floats), at least one photo or placeholder, available variants, and clear stock/availability for the selected variant
- **Given** I am on the product detail screen **when** I use the system or in-app back action **then** I return to the product list without losing the catalog view

### US-003 Add item to in-memory cart (must)
As a mobile shopper, I want to add a selected product variant to a simple in-memory cart from the detail screen, so that I can preview a multi-item bag while checkout remains out of scope for M1.

- **Given** I am on product detail with a variant that has available stock **when** I choose Add to cart **then** the selected variant is added to an in-memory cart and the cart reflects the product name, variant, quantity, and unit price in integer cents USD copied at add time
- **Given** I have one or more items in the in-memory cart **when** I open the simple cart screen or cart view **then** I see each line with name, unit price (cents/USD), quantity, and a line total computed from integer minor units without floating-point money math
- **Given** the app process is restarted **when** I launch the app again **then** the in-memory cart may be empty (persistence is not required in M1) and browsing still works from the mock catalog

## Non-functional requirements
- Android-first Flutter 3.x app must launch on a mainstream Android emulator without a live backend dependency for M1.
- Product list and product detail must render from a local/mock catalog so the demo runs immediately after build/install.
- Prices must be stored and calculated as integer minor units (cents) with ISO 4217 currency code USD; never use floating-point for money.
- Stock awareness is per product variant in the mock data; unavailable variants must be indicated clearly on detail.
- Browse and detail interactions must feel simple for non-technical shoppers: list → detail → optional cart in a few taps.
- UI must remain usable on common phone viewport sizes; text and tap targets must be readable and reachable.
- No card data, passwords, or PII collection in M1; no auth or payment SDKs required for this milestone.
- Style tokens and visual defaults may be chosen by the implementing agent without stakeholder style approval gates.
- M1 scope caps: at most 3 user stories, at most 3 app screens (product list, product detail, optional simple cart), local/mock data only.

## Out of scope
- User authentication, sign-up, sign-in, profiles, and saved addresses
- Guest checkout, checkout flow, order placement, and order status tracking
- Stripe PaymentIntents, webhooks, and any real or test payment confirmation in M1
- Backend API implementation for catalog/cart (prefer local/mock catalog; no NestJS/Prisma work that blocks the Flutter demo)
- Wishlist, push notifications, coupons, loyalty, referrals
- Courier shipping, click-and-collect, returns/refunds, and fulfillment operator workflows
- Admin/merchandiser catalog management UI
- POS, inventory, or accounting system integrations
- iOS as a launch requirement for M1 (Android first)
- Multi-vendor marketplace and third-party seller roles
- Non-USD currencies and non-English languages
- Human approval, stakeholder sign-off, or style-approval work items

## Assumptions
- M1 is a speed demo: a runnable Flutter app with mock catalog supersedes full PRD commerce features until later milestones.
- Browsing does not require sign-in; account features are deferred even though later releases will encourage accounts for history and wishlist.
- Primary market context remains United States, USD, English for display copy in the mock catalog.
- Owned single-brand retail catalog only; mock products represent our brand SKUs.
- In-memory cart is optional but included as the third screen to support US-003; cart is not persisted and cannot complete payment.
- Infrastructure health/docs endpoints and full OpenAPI backend contracts are out of M1 delivery if they slow the Flutter demo; catalog data lives in the app.
- Later phases will add guest checkout, Stripe, order lifecycle (pending_payment → paid → fulfilled → delivered / cancelled / refunded), stock reservation, and admin roles as clarified for the full product.
