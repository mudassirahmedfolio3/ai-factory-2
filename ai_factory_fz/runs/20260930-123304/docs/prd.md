# Simple Shop Mobile App – Speed Demo MVP (Browse and Product Detail)

A deliberately minimal, runnable Flutter demo of the Simple Shop mobile app for a UK retail business. This run delivers only the core browsing journey on an Android emulator: a product list (browse) screen and a product detail screen, both backed by a local/mock catalogue bundled in the app so it runs immediately with no backend, authentication, payments or checkout. An optional simple in-memory cart (add to cart and view cart) is included as a could-have. Prices are held as integer minor units (pence) with ISO 4217 code GBP and displayed tax-inclusive in UK format (e.g. £12.99). Style tokens (colours, typography) are chosen by the development team without waiting on brand approval and kept easy to swap. Scope limits for this run: at most 3 user stories, 3 app screens, 5 work items, 1 milestone. The full brief (accounts, Stripe payments, delivery/pickup, order tracking, push notifications, admin area, reporting) is deferred to later releases.

## Personas
### Sam – New mobile shopper
A customer aged roughly 18-55 who discovers the brand through social media or word of mouth and shops mainly on their phone. Expects a fast, simple app and does not want to sign in just to look at products.
- Browse the catalogue quickly without signing in
- See a product's photo, price, description and stock availability before deciding
- Have a clean, readable, easy-to-tap experience

### Priya – Repeat/existing customer
An existing in-store or online customer who knows the brand and wants a faster way to look through products on their phone. In this demo she only browses and views details, with reorder and history coming later.
- Find familiar products easily in a clear list
- Check price and availability at a glance

### Dev/Product reviewer
A team member or stakeholder who runs the demo on an Android emulator to judge the look, feel and basic flow of the app.
- Run the app immediately on an emulator with no backend or sign-in setup
- See the core browse to detail journey working end to end

## User stories
### US-001 Browse product list (must)
As a shopper, I want to see a scrollable list of products with photo, name and price on launch, so that I can quickly see what the shop sells without signing in.

- **Given** the app is installed on an Android emulator and there is no network or backend available **when** I open the app **then** the product list screen is shown with products loaded from the local mock catalogue, each row showing a thumbnail image, product name and price, with no sign-in prompt
- **Given** the mock catalogue contains at least 10 products with prices stored as integer pence and currency code GBP **when** the product list is displayed **then** each price is formatted tax-inclusive in UK style (for example 1299 pence is shown as £12.99) and no floating-point price values are used in the data model
- **Given** the product list is displayed **when** I scroll through the list **then** scrolling is smooth and all products in the catalogue can be reached
- **Given** the product list is displayed **when** a product has zero stock **then** the row is still shown and is clearly marked as out of stock

### US-002 View product detail (must)
As a shopper, I want to tap a product and see its full details, so that I can decide whether I want to buy it.

- **Given** I am on the product list screen **when** I tap a product **then** the product detail screen opens showing the product's image, name, description, tax-inclusive price in GBP format and stock availability (in stock or out of stock)
- **Given** I am on the product detail screen **when** I use the back button or system back gesture **then** I return to the product list at the same scroll position
- **Given** I am on the detail screen for a product with zero stock **when** the screen is displayed **then** it shows an out of stock indication and any add to cart control is disabled
- **Given** a product has no image available **when** its detail screen or list row is displayed **then** a placeholder image is shown instead and the app does not crash

### US-003 Simple in-memory cart (could)
As a shopper, I want to add products to a basic cart and see what I have added and the total, so that I can get a feel for the buying journey.

- **Given** I am on the detail screen of an in-stock product **when** I tap Add to cart **then** the item is added to an in-memory cart, a confirmation is shown, and a cart item count is visible on the screen
- **Given** I have added one or more items to the cart **when** I open the cart screen **then** each line shows product name, quantity and unit price, and the cart total is shown as the sum calculated in integer pence and formatted as £x.xx
- **Given** the cart contains items **when** I remove an item or change its quantity **then** the cart lines and total update immediately
- **Given** I have items in the cart **when** I fully close and relaunch the app **then** the cart is empty, because it is held in memory only and not persisted

## Non-functional requirements
- Platform: Flutter 3.x (Dart) app that runs on an Android emulator first; iOS support is not validated in this run but nothing should block it later.
- Performance: cold start to the visible product list within 3 seconds on a typical emulator; list scrolling stays smooth with a catalogue of at least 300 mock products; images are loaded lazily.
- Data: the product list reads from a local mock catalogue behind a repository interface so it can later be swapped for the real API without UI changes; no network calls are required to run the app.
- Money: prices are stored as integer minor units (pence) with ISO 4217 currency code GBP, never floats; displayed tax-inclusive in UK format.
- Security and privacy: no authentication, no personal data, no payment data and no card details are collected or stored in this run.
- Accessibility: support dynamic text sizing, screen reader labels (TalkBack) on all buttons, images and interactive elements, colour contrast in line with WCAG 2.1 AA, and comfortably sized touch targets (at least 48x48 dp).
- Theming: style tokens (colours, typography, spacing) are defined centrally in one theme file, chosen by the development team with a clean neutral look, and are easy to swap; no brand or style sign-off is needed.
- Language and locale: English (UK) only, GBP only.
- Quality: the app builds and runs with a single flutter run command; includes basic flutter_test widget tests for the list and detail screens.
- Reliability: the app handles missing images, empty catalogue (shows an empty state message) and out-of-stock products without crashing.

## Out of scope
- User sign-up, login, password reset, email verification and any authentication
- Guest checkout and persisted carts
- Checkout, payments, Stripe integration, Apple Pay and Google Pay
- Delivery address management, home delivery and in-store pickup
- Order placement, order confirmation, order tracking, order history and one-tap reorder
- Backend API work (NestJS, Prisma, PostgreSQL), stock reservation and real stock management
- Search, filters and categories
- Wishlist or favourites
- Push notifications (transactional and promotional)
- Admin web area, staff roles, bulk CSV import and sales reporting
- Refunds, returns flow and customer support chat; Help/Contact screen
- POS/stock system integration
- Loyalty, promo codes and discounts
- Multiple countries, currencies and languages
- Account deletion and other account-related privacy features (no personal data is held in this run)
- Formal WCAG audit and iOS release build

## Assumptions
- The deliverable is a runnable demo on an Android emulator; the choice of Android first follows the target stack.
- A local mock catalogue of roughly 10-20 products (with the ability to scale to 300+ for performance checks) is bundled with the app, with placeholder or bundled images created by the development team.
- Mock product data follows the project rules: integer pence prices, currency GBP, tax-inclusive display, and a stock quantity per product.
- The in-memory cart (US-003) is optional and is delivered only if time allows; US-001 and US-002 are the must-haves.
- The app has three screens at most: product list, product detail and (optional) cart.
- No human approval, stakeholder sign-off or style approval is required at any point; the agent chooses style tokens and proceeds.
- Earlier customer decisions (UK, GBP, English UK, email-and-password sign-in, Stripe, admin web app, flat £3.99 delivery free over £40, etc.) still stand for later releases but are not built in this run.
- Because no backend is built in this run, the health check endpoint and OpenAPI contract are not required for the demo; they will be introduced when the backend work starts.
