# ShopEase Mobile Shopping App: First UI Demo (Browse, Product Detail, Cart)

ShopEase is a simple, fast mobile shopping app for Android and iOS (Android first) for our clothing and accessories store. This PRD covers the first UI demo slice of the MVP: a customer registers or signs in, browses products by category and subcategory, searches by keyword, opens a product detail page with photos, sizes and colors, and manages a shopping cart. The store launches in the United States in USD only, and an account is required to add items to the cart (guest carts are out of scope). Payments, checkout, orders, order history, the staff web admin and transactional emails are deliberately excluded from this run and stay in the wider MVP plan (target launch end of January 2027). Prices are stored as integer cents with currency code USD and are displayed before sales tax. The cart summary shows subtotal, shipping (flat $5.00, free for subtotals of $75.00 or more), sales tax (flat configured rate) and total. Catalogue data (about 300 products, about 2,000 size/color variants, up to 6 photos per product) comes from existing product data loaded into the system for the demo. The slice is limited to 5 app screens (Sign in/Register, Category browse and product list with search, Product detail, Cart, and a simple Home/category entry within the browse screen flow), at most 10 API operations plus a health check, and 6 user stories.

## Personas
### Style-conscious shopper (new or existing customer)
Customer aged 18-45 who shops on their phone, is comfortable with online card payments, and wants to find clothing and accessories quickly and put them in a cart in a few taps.
- Find products quickly by category or keyword search
- See photos, sizes, colors and price on a clear product page
- Know which sizes and colors are available before choosing
- Add items to a cart, adjust quantities and see a clear total including shipping and tax

### Repeat customer
Returning customer who keeps an account and expects to sign in once and find their cart waiting on their next visit.
- Sign in with email and password
- Find their cart contents still saved after signing out and in again

### Store staff / merchandising (secondary, not served in this run)
Internal staff who fulfil orders and maintain the catalogue. The staff web admin, order management and CSV import are out of scope for this run; catalogue data is loaded by the development team for the demo.
- Later releases: view and update orders in a web admin
- Later releases: keep catalogue, prices and stock up to date through CSV import

## User stories
### US-001 Register and sign in with email and password (must)
As a shopper, I want to create an account and sign in with my email and password, so that I can add items to a cart that is saved to my account.

- **Given** I am not signed in and I am on the Sign in/Register screen **when** I submit a valid name, an email address not yet registered, and a password of at least 8 characters **then** my account is created, I am signed in, and I am taken back to where I was in the app
- **Given** I already have an account **when** I enter my correct email and password and tap Sign in **then** I am signed in and my previously saved cart is available
- **Given** I am on the Sign in screen **when** I enter a wrong password or an unknown email **then** I see a generic 'Incorrect email or password' message that does not reveal which of the two was wrong, and I stay signed out
- **Given** I am on the Register screen **when** I submit an email that is already registered, an invalid email format, or a password shorter than 8 characters **then** the account is not created and I see a clear field-level error message for the problem
- **Given** I am signed in and then close and reopen the app **when** the app starts and my session is still valid **then** I remain signed in without re-entering my credentials

### US-002 Browse products by category and subcategory (must)
As a shopper (signed in or not), I want to browse clothing and accessories by category and subcategory and see a list of products, so that I can discover items without knowing exactly what I am looking for.

- **Given** I am on the browse screen and I am not signed in **when** I open the app and select a category, then a subcategory **then** I see a list of products in that subcategory, each showing its main photo, name and price in USD (for example $29.99) before tax
- **Given** a category has more products than fit on one screen **when** I scroll to the bottom of the list **then** the next page of products loads automatically until all products are shown, without duplicates
- **Given** I am viewing a product list **when** I choose to sort by price low to high, price high to low, or newest **then** the list is reordered accordingly (sorting is a should-have for this run)
- **Given** a subcategory contains no products **when** I open it **then** I see an empty-state message instead of a blank screen
- **Given** the product list request fails because of a network or server error **when** I am on the list screen **then** I see an error message with a Retry button, and tapping Retry reloads the list

### US-003 Search products by keyword (should)
As a shopper (signed in or not), I want to search products by keyword, so that I can quickly find a specific item.

- **Given** I am on the browse screen **when** I enter a keyword such as 'denim' and submit the search **then** I see a list of products whose name or description contains the keyword (case-insensitive), in the same card format as the category list
- **Given** I submit a keyword that matches no products **when** the search completes **then** I see a 'No products found' message and can edit the keyword and search again
- **Given** I submit an empty or whitespace-only search **when** I tap search **then** no search is run and I keep seeing the current list

### US-004 View product details with sizes and colors (must)
As a shopper (signed in or not), I want to open a product and see its photos, description, price and available sizes and colors, so that I can decide what to buy and choose the right variant.

- **Given** I am on a product list **when** I tap a product **then** the Product detail screen shows its name, description, price in USD before tax, a photo gallery I can swipe through (up to 6 photos), and the available sizes and colors
- **Given** a size/color variant is out of stock **when** I view the size and color selectors **then** that variant is shown greyed out and cannot be selected, while in-stock variants can be selected
- **Given** every variant of the product is out of stock **when** I open the product **then** an 'Out of stock' label is shown and the Add to cart button is disabled
- **Given** I have not yet selected a size and color **when** I look at the Add to cart button **then** it is disabled until a size and a color combination that is in stock has been selected
- **Given** I open a product that no longer exists **when** the server returns not found **then** I see a 'Product not found' message with a way back to the list

### US-005 Add a product variant to my cart (must)
As a signed-in shopper, I want to add a selected size and color of a product to my cart, so that I can collect the items I want to buy.

- **Given** I am signed in and have selected an in-stock size and color on the Product detail screen **when** I tap Add to cart **then** the variant is added to my cart with quantity 1, a confirmation is shown, and the cart badge count updates
- **Given** the same variant is already in my cart **when** I add it again **then** the existing cart line quantity increases by 1 instead of creating a second line
- **Given** I am not signed in **when** I tap Add to cart **then** I am taken to the Sign in/Register screen, and after signing in I return to the same product so I can add it
- **Given** the quantity of a variant in my cart already equals its available stock **when** I tap Add to cart again **then** the quantity does not increase and I see a message that no more units are available

### US-006 View and edit my cart (must)
As a signed-in shopper, I want to see my cart, change quantities, remove items and see the order totals, so that I know exactly what I would pay before I continue.

- **Given** I am signed in and have items in my cart **when** I open the Cart screen **then** each line shows the product name, photo, size, color, unit price, quantity and line total, and a summary shows subtotal, shipping, sales tax and total, all in USD
- **Given** my cart subtotal is under $75.00 (7500 cents) **when** the summary is calculated **then** shipping is shown as $5.00 and is added to the total
- **Given** my cart subtotal is $75.00 (7500 cents) or more **when** the summary is calculated **then** shipping is shown as $0.00 (free) and the total excludes any shipping charge
- **Given** the cart contains items **when** I increase or decrease the quantity of a line within 1 and the available stock **then** the line total and the summary update immediately and the change is saved to my account
- **Given** a cart line is shown **when** I remove it, or reduce its quantity below 1 by confirming removal **then** the line disappears and the summary is recalculated
- **Given** my cart is empty **when** I open the Cart screen **then** I see an empty-cart message with a button to continue shopping
- **Given** I sign out and sign in again on the same or another device **when** I open the Cart screen **then** my cart lines are still present

## Non-functional requirements
- Platforms: Flutter app for Android 10 and later and iOS 16 and later; Android is built and tested first, iOS follows with the same codebase. Single language: English.
- Performance: product list and product detail screens show content within 2 seconds on a typical 4G connection for the catalogue of about 300 products and 2,000 variants; list pages are paginated; photos are loaded lazily and cached on the device; backend responses for list, detail and cart operations are under 500 ms at the 95th percentile under demo load.
- Money: all prices, line totals, shipping, tax and totals are stored and calculated as integer minor units (cents) with ISO 4217 currency code USD, never floats. Sales tax is computed from a single flat rate configured for the home state, rounded half up to the nearest cent, and shown as a separate line. Prices are displayed before tax.
- Stock: stock is tracked per product variant. The cart does not reserve stock in this run; stock is reserved only at checkout in a later release. Quantities in the cart may never exceed the available stock at the time they are set.
- Security: passwords are hashed with bcrypt or argon2 and never stored or logged in plain text; authentication uses JWT with an expiry; all cart endpoints require authentication and only return or modify the caller's own cart; all traffic uses HTTPS outside local development; input is validated on the server; no card data is handled in this run.
- Privacy: collect the minimum personal data, limited in this run to name, email and password hash. No date of birth, gender or other personal data. No analytics that identify individuals without consent.
- Accessibility: interactive elements have accessible labels for screen readers (TalkBack and VoiceOver), touch targets are at least 48x48 dp, text respects the system font size setting, colour is not the only way to show out-of-stock state (greyed out variants also carry a text or accessibility label 'Out of stock'), and contrast meets WCAG AA.
- Usability: the app is simple, clean and usable by non-technical shoppers; every screen handles loading, empty and error states with a retry option.
- Reliability and operability: the backend exposes a health check endpoint (GET /health) and an OpenAPI document (/api/docs-json) as infrastructure endpoints; the API contract is published via OpenAPI and the mobile API client is generated from it.
- Scope limits for this run: at most 6 user stories, 10 work items, 2 milestones, 10 API operations (excluding /health and /api/docs-json) and 5 app screens (Sign in/Register, Category browse, Product list with search and sort, Product detail, Cart).
- Testability: each acceptance criterion is verifiable by QA; backend logic is covered by Jest and Supertest tests and the core journey (sign in, browse, open product, add to cart, edit cart) by a Flutter integration test.

## Out of scope
- Payments, checkout, Stripe PaymentIntents and webhooks, stock reservation, and Apple Pay / Google Pay (card payments via Stripe test mode are planned for the wider MVP; Apple Pay / Google Pay come after the first release)
- Orders, order history and order statuses (pending_payment, paid, fulfilled, delivered, cancelled, refunded) and customer-facing status labels
- Staff and admin web admin, staff accounts and roles, order management, tracking numbers
- CSV catalogue import, scheduled or manual re-import and any catalogue create/edit back-office (demo data is loaded by the development team)
- Guest browsing with guest carts or guest checkout (browsing and search are open to anonymous users, but the cart requires sign-in)
- Email verification, password reset emails, order confirmation and shipping emails and any other transactional email (required before first checkout or public launch, not in this run)
- In-app account deletion and anonymised retention of past orders (required by app store rules and privacy conventions before public launch, not in this run)
- Marketing consent checkbox at registration, marketing messages and campaigns
- Shipping address entry, saved default address, address book, and international shipping
- Returns and refunds flow, return policy and support contact screens
- Push notifications
- Filters by size, color and price range; 'Notify me' for out-of-stock items; wishlists, discount codes, loyalty points and reviews
- Social sign-in (Google, Apple)
- Automated multi-state tax calculation
- Multiple languages and multiple currencies
- Production Stripe account set-up and public store release

## Assumptions
- Launch market is the United States with USD as the single currency; international shipping is out of scope.
- Shipping is one standard option at a flat $5.00, free when the subtotal is $75.00 or more; it is shown in the cart summary as information, and shipping address entry happens at checkout in a later release.
- Sales tax uses one flat rate for the home state, configured on the server; the exact rate is to be provided by the client before build (a placeholder value is used in the demo). Tax is shown as a separate line in the cart summary.
- The cart requires a signed-in user; guest carts are out of scope. Browsing, search and product details are available without signing in.
- Catalogue data (about 300 products, about 2,000 variants, prices, stock, photo URLs with up to 6 photos per product) is provided as seed or sample data and loaded into PostgreSQL by the development team; photos are hosted as image files referenced by URL.
- Categories have one level of subcategories (for example Clothing > Tops, Accessories > Bags).
- Password rule for the demo is a minimum of 8 characters; email addresses must be unique and are stored case-insensitively.
- Out-of-stock variants are shown greyed out and unselectable; if all variants are out of stock, an 'Out of stock' label is shown and Add to cart is disabled.
- Cart quantity per line is limited by the variant's available stock and has no other fixed maximum in this run.
- Android is built and tested first; iOS uses the same Flutter codebase with a minimum of iOS 16, and Android minimum is Android 10.
- Target launch of the wider MVP is end of January 2027; this run delivers a first UI demo only. Success targets for the first 3 months after launch (5,000 downloads, 1,500 registered accounts, 600 paid orders, at least 2% browse-to-paid conversion, 20% repeat-customer orders, 30% fewer 'where is my order' emails) apply to the full MVP, not to this demo.
