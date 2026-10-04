# beauty-mini: Flutter Beauty Shop Speed Demo (M1)

The smallest possible Flutter beauty shop demo that runs on an Android emulator in under 10 minutes. It shows the core shopping experience (browse products, view a product, add to cart) using hard-coded local data, so the team gets a quick, tangible feel for the app before investing in a full build. Scope for this milestone is limited to 3 user stories and 3 app screens at most: a browse screen (grid of 8 hard-coded products with name, price in USD, and placeholder color), a product detail screen (name, price, short description), and an optional in-memory add-to-cart with a cart count badge on the browse app bar. There is no backend, no auth, no payments, no checkout, and no API integration; `flutter run` works right after scaffold. No work item waits on human, style or stakeholder approval; the team picks sensible defaults (for example style tokens) and keeps moving. Prices are kept as integer minor units (cents) with currency code USD per project convention, never floats. No API operations are required in this milestone; since there is no backend, no /health endpoint is implemented and the local catalog is bundled in the Flutter app.

## Personas
### Internal team member (business owner, merchandising, marketing)
Me and my internal team who need to see a working beauty shopping app quickly and react to something concrete.
- See a working beauty shopping app in under 10 minutes
- Validate the basic browse-to-detail-to-cart flow
- Decide what to build in the next milestone

### Developer / designer
Developers and designers who run the demo on an Android emulator and build on it in later milestones.
- Run the app with `flutter run` right after scaffold with no setup, backend or network
- Have a simple, clear base structure to extend in later milestones

### Future shopper (not served by this demo)
Beauty-conscious customers browsing on their phones. Not served by this demo, but their needs inform the layout and flow.
- Browse beauty products easily on a phone
- View product details and add items to a cart

## User stories
### US-001 Browse beauty products in a grid (must)
As a internal team member, I want to see a grid of 8 hard-coded beauty products, each showing name, price in USD and a placeholder color, so that I get a quick, tangible feel for the browse experience without any backend or setup.

- **Given** the app has been scaffolded and launched on an Android emulator with no network connection **when** the app opens **then** the browse screen is shown with a grid of exactly 8 products: lipstick, foundation, mascara, face serum, moisturizer, perfume, nail polish and makeup brush set
- **Given** the browse screen is displayed **when** I look at any product tile **then** the tile shows the product name, the price formatted in USD from integer cents (for example 1999 cents is displayed as $19.99) and a placeholder color block instead of an image
- **Given** the project has just been scaffolded **when** I run `flutter run` on an Android emulator **then** the app builds and shows the browse screen without any extra configuration, backend, login or API call, within 10 minutes from start

### US-002 View product detail (must)
As a internal team member, I want to tap a product on the grid and see its name, price and a short description, so that I can validate the browse-to-detail flow.

- **Given** the browse screen is displayed **when** I tap a product tile **then** the product detail screen opens showing that product's name, USD price and a short description
- **Given** the product detail screen is displayed **when** I use the back button or system back gesture **then** I return to the browse screen with the grid still displayed
- **Given** the product detail screen is displayed for any of the 8 products **when** I view it **then** the name and price match the tile I tapped on the browse screen

### US-003 Add to cart with in-memory cart count (could)
As a internal team member, I want an Add to cart button on the product detail screen that keeps items in memory and shows a cart count badge on the browse screen app bar, so that I can see the core browse-to-detail-to-cart flow end to end.

- **Given** I am on a product detail screen and the cart is empty **when** I tap the Add to cart button **then** the cart count increases by 1 and the browse screen app bar badge shows 1 when I return to it
- **Given** the cart already contains items **when** I add another product (or the same product again) **then** the badge count increases by 1 for each tap (counting total items added; no quantity editing or removal is offered)
- **Given** the cart contains one or more items **when** I fully close and restart the app **then** the cart is empty and no badge count is shown, since the cart is in memory only
- **Given** the cart is empty **when** I view the browse screen **then** no badge is shown or the badge shows 0, and no checkout option exists anywhere in the app

## Non-functional requirements
- Platform: Android emulator is the only supported target for this milestone; Flutter 3.x (Dart). iOS support is not required for M1.
- Setup time: a developer can go from scaffold to the running app on an Android emulator in under 10 minutes using `flutter run` with no additional setup.
- Offline: the app works fully offline; all data is hard-coded local data bundled in the app; placeholder colors are used instead of network images.
- Performance: browse screen renders the 8-item grid and navigation to the detail screen feels instant (under 1 second on a typical emulator) with no network calls.
- Money handling: prices are stored as integer minor units (cents) with currency code USD and formatted only for display; floats are never used for prices.
- Security and privacy: the app collects no personal data, has no accounts, no authentication, and makes no network or API calls; no card data or payments of any kind exist.
- Accessibility: product tiles and buttons are tappable with a reasonable touch target size (at least 48x48 dp), text is readable against the placeholder colors, and product names are exposed as semantic labels.
- Maintainability: code structure is simple and clear so developers and designers can extend it in later milestones; style tokens (colors, typography) are chosen by the team without waiting for approval.
- Testability: the browse, detail and cart count behaviors are verifiable manually on an emulator, and can be covered by basic flutter_test widget tests.

## Out of scope
- Authentication, accounts, sign-in and account deletion
- Payments, Stripe integration and checkout flow
- Backend (NestJS, Prisma, PostgreSQL) and any API integration or API operations
- Real product images via URLs (placeholder colors only for now)
- Cart contents screen, tappable cart, cart quantities and removing items
- Persisting the cart across app restarts (cart is in memory only)
- Stock tracking, stock reservation, orders and order statuses
- Guest carts and multi-user carts
- iOS support
- Real product catalog, pricing and currencies other than USD
- Any work item waiting on human, style or stakeholder approval
- Search, filters, sorting, wishlists and reviews

## Assumptions
- Default decision from the brief: 8 hard-coded products with placeholder colors and prices in USD: lipstick, foundation, mascara, face serum, moisturizer, perfume, nail polish and makeup brush set.
- Product prices are illustrative sample values in integer cents with currency USD; the exact amounts are chosen by the team without approval.
- The Add to cart feature is optional (priority could) and is included because it is part of the listed key features; it is cut first if it slows delivery.
- The cart count badge counts total items added, since quantities and removal are out of scope.
- Open questions in the brief (real images, tappable cart, quantities, real catalog, backend timing, iOS) are deferred to after the demo and do not block M1.
- The team picks sensible defaults for style tokens and short product descriptions and keeps moving without waiting for approval.
- No backend or API is built in M1; the local catalog lives in the Flutter app, so no /health endpoint is needed for the demo.
