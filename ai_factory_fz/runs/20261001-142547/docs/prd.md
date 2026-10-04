# PulsePhones Flutter MVP — M1 Product Requirements (Browse & Detail Demo)

PulsePhones is a Flutter Android-first smartphone storefront MVP branded for a clean, modern mobile phone shop. Milestone 1 (speed demo) delivers the smallest runnable app: a local/mock catalog of about 12–20 smartphones, a product list (browse) screen, and a product detail screen so shoppers can scan listings styled like iPhone X ($899.99) and open a product for name, price in USD minor units, key details, and star rating display. An optional in-memory cart with quantity updates may be included as the third screen. No authentication, payments, checkout, order history, or backend API work in M1—the app must run on an emulator immediately from seeded local data. Later releases may add guest checkout, registered accounts, Stripe test payments, reviews posting, and order history; those are explicitly out of scope for this sprint increment.

## Personas
### Mobile smartphone shopper
A value-conscious shopper browsing phones on Android who wants to compare models, prices, and ratings quickly in a demo-ready PulsePhones app without signing in.
- Browse a curated smartphone catalog on mobile
- Open a product to see price, key specs, and star rating social proof
- Optionally adjust cart quantities in memory to try the path toward purchase

### Demo stakeholder / sprint reviewer
A product or engineering stakeholder validating that the Flutter MVP launches on an emulator in one sprint and proves the core browse → detail journey for the smartphones vertical.
- See PulsePhones branding on splash/home and listings
- Confirm seeded catalog listings render with name, price, and ratings
- Verify the app needs no backend for M1 and stays within screen/story limits

## User stories
### US-001 Browse smartphone catalog (must)
As a mobile smartphone shopper, I want to see a scrollable list of seeded smartphones with name, USD price, and star rating, so that I can compare models and pick one to inspect on my phone.

- **Given** the PulsePhones Flutter app is launched on an Android emulator with the local mock catalog loaded **when** I open the product list (browse) screen **then** I see between 12 and 20 smartphone listings, each showing product name, price formatted from integer minor units with currency USD (e.g. $899.99 for 89999 cents), and a visible star rating summary
- **Given** I am on the product list screen **when** I scroll the catalog **then** all seeded products remain reachable without requiring network calls or authentication
- **Given** I am on the product list screen **when** the list finishes rendering **then** the storefront branding displays PulsePhones (not the working project title) and the vertical is limited to smartphones

### US-002 View smartphone product detail (must)
As a mobile smartphone shopper, I want to open a product from the list and see its name, price, key details, and star rating, so that I can evaluate a phone with enough information to decide interest before any checkout is built.

- **Given** I am on the product list screen with seeded smartphones visible **when** I tap a product listing **then** I navigate to the product detail screen for that product showing name, USD price from integer cents, key details, and star rating
- **Given** I am on a product detail screen **when** I use the back/navigation control **then** I return to the product list without losing the local catalog state
- **Given** a seeded product has a display price of 89999 cents USD **when** I view that product on the detail screen **then** the price is shown as $899.99 (or equivalent locale formatting for USD) and never as a floating-point storage value in the mock data model

### US-003 Manage simple in-memory cart quantities (should)
As a mobile smartphone shopper, I want to add a phone to an in-memory cart and change quantities (increase, decrease, remove), so that I can try a lightweight path from browse toward purchase without auth or payments in M1.

- **Given** I am on a product detail screen for an in-stock seeded smartphone (stock assumed always available) **when** I add the product to the cart **then** an in-memory cart contains that line with quantity 1 and I can open a simple cart screen showing the line
- **Given** my in-memory cart has a line with quantity greater than 1 **when** I decrease quantity or remove the line **then** the cart updates immediately in memory and reflects the new quantity or omits the removed line without calling a backend
- **Given** the app process is killed or restarted **when** I reopen PulsePhones **then** the in-memory cart is empty (persistence, guest checkout, and payment are not required in M1)

## Non-functional requirements
- Android-first Flutter 3.x app must launch on an emulator without a live backend; catalog and ratings data come from local/mock seed data.
- Product prices are represented as integer minor units (cents) plus ISO 4217 code USD in models; UI formats for display only—never store floats.
- Browse and detail screens should feel mobile-first: readable prices, clear product imagery placeholders or assets, and star ratings prominent on list and detail.
- M1 cold start to interactive product list should be suitable for a one-sprint demo (target under ~3 seconds on a typical emulator with local data).
- No collection of passwords or personal account data in M1; if any future auth is added later, passwords must use bcrypt or argon2 and support account deletion—out of scope for this milestone.
- Accessibility: text contrast and tap targets usable for primary browse/detail actions; semantic labels on list items and primary buttons where practical.
- Scope caps for this run: at most 3 user stories, at most 3 app screens (list, detail, optional cart), at most 1 milestone, at most 4 API operations if any stub exists; prefer zero commerce APIs in M1. Infrastructure /health (and /api/docs-json if present) do not count toward the API operation limit.
- Style tokens and PulsePhones visual identity may be chosen by the implementing agent without human style approval gates.

## Out of scope
- User authentication, sign-up, sign-in, forgot-password, and registered accounts for M1
- Guest checkout, payment (Stripe or simulated card), checkout confirmation, and order placement
- Order history, fulfilment, refunds, and order status workflow
- Backend NestJS/Prisma/PostgreSQL feature work required to run the M1 demo; live OpenAPI-backed catalog for M1
- CSV import, admin product entry, and catalog management tooling
- Inventory tracking, stock reservation, low-stock alerts, and out-of-stock blocking (assume all seeded phones available)
- Review posting/moderation workflows (display of seeded star ratings on list/detail is enough for M1; post-purchase-only rules deferred)
- Apple Pay, Google Pay, cash on delivery, multi-currency, multi-country tax, and complex shipping rules
- Desktop/web clients, multi-vendor marketplace, loyalty, and personalization
- Email/push notifications and advanced account recovery
- Any work item that requires human approval, stakeholder sign-off, or style approval before coding

## Assumptions
- Brand name for splash/home and storefront chrome is PulsePhones.
- Initial catalog is a manual seed of approximately 12–20 smartphones with name, integer USD cents price, key details, and star rating fields suitable for list/detail display.
- Stock is assumed available for all seeded products in M1; no inventory service.
- Single English-language, USD-only market for display.
- M1 may use zero commerce API operations; if a minimal Nest stub exists, only infrastructure health (and docs-json) are expected—commerce endpoints are deferred.
- In-memory cart is optional but, if shipped, counts as the third app screen and does not persist across process restarts.
- Full PRD features from the original brief (guest checkout, accounts, Stripe PaymentIntents, review posting, order history) are deferred to later milestones after this speed-demo increment validates browse/detail on Flutter.
