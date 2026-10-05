# Lighting E-Commerce Mobile App – Speed Demo MVP (Browse, Product Detail, In-Memory Cart)

Speed demo of the lighting shopping app: the smallest runnable Flutter app that runs on an Android emulator immediately using a local/mock catalog bundled in the app. It has three screens: Product List (browse), Product Detail, and a simple in-memory Cart. There is no authentication, no payments, no checkout and no backend API work in this run. Prices are stored as integer minor units (pence) with ISO 4217 currency code GBP and formatted for display only; prices shown include 20% VAT. Lighting-specific specifications (wattage, lumens, color temperature, IP rating, dimmable, etc.) are shown on the product detail screen. Style tokens (colors, typography, spacing) are chosen by the development agent without waiting for approval. The mock catalog is a hand-written seed of a few representative lighting products across categories. Target platform is Android first (Flutter 3.x, Riverpod, go_router). Guest carts, guest checkout, Stripe payments, COD, bank transfer, order management, admin dashboard and all P1 features from the full brief are deferred to later milestones.

## Personas
### Mobile-first homeowner or renter
A UK homeowner or renter browsing lighting products on their phone to find and compare products before buying. In this demo they use the app as a guest with no sign-in.
- Quickly browse a list of lighting products with image, name, price and stock status
- Open a product to see price and lighting specifications such as wattage, color temperature and IP rating
- Add products to a simple cart and see the subtotal

### Demo reviewer / stakeholder
Internal team member who runs the app on an emulator to see the core browse-to-detail-to-cart journey working end to end.
- Launch the app on an Android emulator with no backend or account setup
- See a realistic lighting catalog and a working core journey

## User stories
### US-001 Browse product list (must)
As a shopper, I want to see a scrollable list of lighting products with image, name, price and stock status, so that I can quickly find a product that interests me.

- **Given** the app is installed on an Android emulator with no network connection and no backend **when** I launch the app **then** the Product List screen opens and shows the products from the bundled local mock catalog, each with image, name, price formatted in GBP from integer pence, and a stock status label (In stock, Low stock when 5 or fewer units, or Out of stock)
- **Given** the Product List screen is showing the catalog **when** I scroll the list **then** the list scrolls smoothly, product images load lazily, and each product card is tappable
- **Given** a product on the list has a sale price **when** the list renders that product **then** both the original price (struck through) and the sale price are displayed, and the sale price is lower than the original price
- **Given** the mock catalog contains at least 10 products across multiple lighting categories **when** I view the Product List screen **then** at least 10 products are displayed, and every product shows a non-empty name and a price greater than zero

### US-002 View product detail with lighting specifications (must)
As a shopper, I want to open a product and see its full details and lighting specifications, so that I can decide whether it fits my needs.

- **Given** I am on the Product List screen **when** I tap a product card **then** the Product Detail screen opens for that product showing image, name, SKU, brand, price (and sale price if applicable), description, stock status and a quantity selector
- **Given** I am on the Product Detail screen for a product with specifications **when** I view the specifications section **then** the available lighting specifications (for example wattage, lumens, color temperature, voltage, light type, dimmable, material, finish, dimensions, weight, IP rating, bulb type, bulb included) are listed as label and value pairs, and specifications not applicable to the product are not shown
- **Given** I am on the Product Detail screen **when** I press the back button or the back control in the app bar **then** I return to the Product List screen at the same scroll position
- **Given** I am on the Product Detail screen for an out-of-stock product **when** the screen renders **then** the stock status shows Out of stock and the Add to cart button is disabled

### US-003 Add products to a simple in-memory cart (should)
As a shopper, I want to add products to a cart and see quantities and the subtotal, so that I can see what I intend to buy.

- **Given** I am on the Product Detail screen for an in-stock product and have selected a quantity **when** I tap Add to cart **then** the selected quantity of that product is added to the in-memory cart, a confirmation is shown, and a cart badge or entry point shows the updated item count
- **Given** the cart contains one or more items **when** I open the Cart screen **then** each line shows product name, unit price, quantity and line total, and the subtotal equals the sum of line totals, computed using integer pence and displayed in GBP
- **Given** the Cart screen shows an item **when** I change its quantity to a new valid value or remove it **then** the line total and subtotal update immediately, and removing the last item shows an empty-cart message
- **Given** a product has limited stock in the mock catalog **when** I try to set a quantity above the available stock **then** the quantity is capped at the available stock and a message explains the limit
- **Given** I have items in the cart **when** I fully close and relaunch the app **then** the cart is empty, because the cart is held in memory only

## Non-functional requirements
- Platform: Flutter 3.x (Dart) app, Android first; must run on a standard Android emulator with no additional setup, backend or account
- Startup and performance: app reaches the Product List screen within 3 seconds on a mid-range emulator; list scrolling stays smooth; product images are lazy loaded
- Offline-capable by design: the demo uses a local/mock catalog bundled in the app and requires no network
- Money handling: prices are stored and computed as integer minor units (pence) with ISO 4217 currency code GBP; floats are never used for money; prices are displayed formatted as GBP and include 20% VAT
- Data model: mock product data includes id, SKU, name, brand, category, price in pence, optional sale price in pence, stock quantity, description, image reference and a map of lighting specifications
- Low-stock rule reflected in UI: a single global threshold of 5 units
- Security and privacy: no authentication, no payment data and no personal data are collected or stored in this demo; no network calls are made
- Accessibility: tappable elements have a minimum 48x48 dp touch target, text respects the system font scale, images have semantic labels, and color contrast meets WCAG AA
- Usability: clear loading, empty and error states on each screen; language is English only
- Maintainability: state managed with Riverpod, navigation with go_router, immutable models with freezed; the catalog sits behind a repository interface so a real API client can replace the mock later
- Testing: flutter_test unit tests for price formatting and cart arithmetic, and widget tests covering list-to-detail navigation and add to cart
- Design: style tokens (colors, typography, spacing) are selected by the development agent with no approval step

## Out of scope
- User registration, login, logout, password reset and any authentication (including guest account creation)
- Checkout, shipping methods, shipping cost calculation, VAT breakdown, order creation, order confirmation and order history
- Payments of any kind: Stripe, card, cash on delivery and bank transfer
- Backend API, database and any server-side work (NestJS, Prisma, PostgreSQL); no API operations are built in this run
- Admin dashboard, product, inventory and order management, CSV import
- Search, search suggestions, recent searches, sorting and filters
- Product variants and variant-level inventory
- Home screen with banners, featured products and category navigation
- Wishlist, reviews and ratings, push notifications, coupons and promotions, customer support, analytics
- Persisting the cart across app restarts, guest cart merge on sign-in
- iOS release builds, localization, multiple currencies, social login, loyalty points, gift cards, AR and live chat
- Any task requiring human approval, stakeholder sign-off or style approval

## Assumptions
- The scope of this run is a speed demo limited to at most 3 user stories, 5 work items, 1 milestone and 3 app screens (Product List, Product Detail, Cart); the Cart screen is optional and may be cut first if delivery is at risk
- The catalog is a local/mock dataset bundled in the Flutter app (for example a Dart or JSON asset with about 10 to 15 lighting products across categories such as ceiling lights, pendants, wall lights, table/floor lamps, bulbs, outdoor and smart lighting)
- Because no backend is built in this run, no API operations are required; the health check and OpenAPI contract are deferred until backend work begins
- Product images are bundled placeholder assets or generated placeholders so the app runs offline
- Currency is GBP and prices include 20% VAT, matching the launch market answers in the full brief; the VAT breakdown display is deferred to checkout work
- Low stock is a single global threshold of 5 units, per the clarified rules
- Development and verification target an Android emulator; iOS is expected later from the same Flutter codebase
- Decisions on style tokens are made by the development agent without stakeholder approval
- Guest checkout, Stripe payments, COD, bank transfer, order statuses (Pending, Confirmed, Processing, Shipped, Delivered, plus Cancelled) and payment statuses are captured in the clarifications and deferred to later milestones
