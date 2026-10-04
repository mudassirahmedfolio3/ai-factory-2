# beauty-mvp: Mobile Beauty Shopping App (First Demo) – Product Requirements Document

beauty-mvp is a simple, attractive Flutter mobile app (iOS and Android from one codebase) that lets beauty shoppers browse a sample catalog of about 24 products across four categories (skincare, makeup, haircare, fragrance), view product details with size or shade options, and add items to an in-memory cart that shows a running subtotal in US dollars. It is a deliberately small demo, built in about 3 to 4 weeks, to prove the core shopping experience to internal stakeholders (owner, sales and marketing leads) and early users before investing in a full ecommerce platform. Scope is limited to three screens: Product List, Product Detail and Cart. Product data comes from a local or mock source, with no backend, accounts, checkout, payments or order processing. The Checkout button in the cart is a placeholder that only shows a 'coming soon' message. The demo is shown on physical phones (one iPhone and one Android phone), with emulators as backup. iOS is the priority if time gets tight, but the app must still run correctly on Android.

## Personas
### Beauty Shopper (Mia)
A customer aged 18-40 who buys skincare, makeup and haircare products on her phone and wants a fast, pleasant way to browse the catalog. Includes existing customers of the retail business who find the current channels slow.
- Quickly browse products with clear images, names, brands and prices
- Narrow the catalog to a category of interest
- See full product details and pick a size or shade
- Collect items in a cart and see what the total would be

### Internal Stakeholder Reviewer (owner, sales or marketing lead)
A business stakeholder who will review the first demo on a physical phone and give feedback to decide the next phase of features and budget.
- See a working, polished demo of browse, detail and cart that reflects the brand
- Judge whether the browsing and cart experience is easy and appealing
- Give concrete feedback to guide next-phase scope and budget

## User stories
### US-001 Browse the product list (must)
As a beauty shopper, I want to scroll through a list or grid of beauty products showing image, name, brand and price, so that I can quickly see what the brand offers and pick something to look at more closely.

- **Given** the app is launched and the sample catalog of about 24 products is loaded from the local or mock data source **when** the Product List screen is displayed **then** a scrollable list or grid shows every product with its image, name, brand and price formatted in US dollars (for example $24.00), and all 24 products can be reached by scrolling
- **Given** a product has no supplied image yet **when** its product card is displayed **then** a neutral placeholder image is shown in place of the product image and the card layout is not broken
- **Given** the Product List screen is displayed **when** the user taps a product card **then** the Product Detail screen for that product opens, and the back action returns to the list at the same scroll position

### US-002 Filter products by category (must)
As a beauty shopper, I want to filter the product list by category (skincare, makeup, haircare, fragrance), so that I can focus on the type of product I am interested in.

- **Given** the Product List screen is displayed with all products **when** the user selects the 'Makeup' category filter **then** only makeup products are shown, the selected filter is visibly highlighted, and products from other categories are hidden
- **Given** a category filter is active **when** the user selects 'All' or taps the active filter again to clear it **then** all products from all four categories are shown again
- **Given** the Product List screen is displayed **when** the user views the available filters **then** exactly four category filters (skincare, makeup, haircare, fragrance) plus an 'All' option are offered, and no search box or sort control is present

### US-003 View product details and choose a size or shade (must)
As a beauty shopper, I want to open a product page with larger images, name, price, description and size or shade options where they apply, so that I understand the product and can choose the option I want before adding it to my cart.

- **Given** the user has opened a product from the list **when** the Product Detail screen loads **then** it shows the larger product image(s), name, brand, price in US dollars, description, and an Add to Cart button
- **Given** the opened product is a makeup product with shade options **when** the Product Detail screen loads **then** a shade selector is shown, no size selector is shown, and the user can select exactly one shade at a time
- **Given** the opened product is a skincare or haircare product with size options **when** the Product Detail screen loads **then** a size selector is shown, no shade selector is shown, and the user can select exactly one size at a time
- **Given** the opened product has no size or shade options **when** the Product Detail screen loads **then** no variant selector is displayed and the Add to Cart button is enabled
- **Given** the opened product has a size or shade selector and none is selected yet **when** the user taps Add to Cart **then** the item is not added and a message asks the user to choose a size or shade, unless a default option is preselected

### US-004 Add a product to the cart (must)
As a beauty shopper, I want to tap Add to Cart on the product page and have the item appear in my cart, so that I can collect the products I am interested in.

- **Given** the user is on a Product Detail screen with a valid selection (or no variants apply) **when** the user taps Add to Cart **then** the product is added to the cart with quantity 1 and the chosen size or shade recorded on the cart item, the user gets a brief confirmation (for example a snackbar), and the cart icon shows the updated total item count
- **Given** the cart already contains the same product with the same size or shade **when** the user adds that product and variant again **then** the existing cart line quantity increases by 1 instead of creating a duplicate line
- **Given** the cart already contains a product with one shade or size **when** the user adds the same product with a different shade or size **then** a separate cart line is created for the new variant choice
- **Given** items have been added to the cart **when** the user fully closes and relaunches the app **then** the cart is empty, because the cart is held in memory only and is not persisted

### US-005 Manage the cart and see a running subtotal (must)
As a beauty shopper, I want to view my cart items, change quantities, remove items and see a running subtotal, so that I can review and adjust what I have chosen and see what it would cost.

- **Given** the cart contains one or more items **when** the user opens the Cart screen **then** each line shows the product image, name, brand, chosen size or shade (if any), unit price, quantity and line total, and a subtotal for all lines is shown in US dollars
- **Given** the Cart screen is displayed with a line at quantity 2 **when** the user taps the increase quantity control **then** the quantity becomes 3, the line total and the subtotal update immediately, and the cart icon count updates
- **Given** the Cart screen is displayed with a line at quantity 1 **when** the user views the decrease quantity control **then** the decrease control is disabled, so quantity never drops below 1 and the user must use Remove to delete the line
- **Given** the Cart screen is displayed with multiple lines **when** the user taps Remove on one line **then** only that line is removed and the subtotal is recalculated correctly from the remaining lines
- **Given** the cart contains a product priced $19.99 at quantity 3 and a product priced $8.50 at quantity 1 **when** the Cart screen is displayed **then** the subtotal shows $68.47, calculated from integer cent amounts (1999 x 3 + 850 = 6847) with no rounding error
- **Given** the cart is empty **when** the user opens the Cart screen **then** an empty-state message is shown with an action that returns to the Product List, and the Checkout button is not shown or is disabled

### US-006 Placeholder Checkout button (should)
As a stakeholder reviewer, I want to see a Checkout button in the cart that clearly indicates checkout is not part of this demo, so that I can understand where checkout will fit in the future experience without any real order or payment flow.

- **Given** the cart contains at least one item **when** the user views the Cart screen **then** a Checkout button is visible below the subtotal
- **Given** the Cart screen shows the Checkout button **when** the user taps Checkout **then** a short message such as 'Checkout is coming soon. This is a demo.' is displayed and the user stays on the Cart screen with the cart contents unchanged
- **Given** the user has tapped the Checkout button **when** the app is inspected during testing **then** no payment screen, account or sign-in screen, order creation or network call is triggered

## Non-functional requirements
- Supported platforms: iOS and Android, built from a single Flutter 3.x codebase. The demo is shown on one physical iPhone and one physical Android phone, with emulators as backup. If time is tight, iOS is the priority for the stakeholder meeting, but the app must still run correctly on Android.
- Performance: the Product List loads and displays within 2 seconds of app launch on the demo devices with the 24-product sample catalog, scrolling stays smooth without visible jank, and images are sized appropriately and cached so they do not cause noticeable delays.
- Performance: cart actions (add, change quantity, remove) update the screen and subtotal within 300 ms.
- Data: the catalog is loaded from a local or mock data source bundled with the app; no backend, live inventory or network connection is required to run the demo.
- Money handling: prices are stored as integer minor units (cents) together with an ISO 4217 currency code (USD) and are never floats. Subtotals are computed in integer cents and formatted as US dollars only for display.
- Cart state: the cart is held in simple in-memory state only and resets when the app is closed.
- Accessibility: use readable text sizes, good color contrast, and tappable areas large enough for comfortable use (at least 44x44 pt / 48x48 dp). Full accessibility compliance is not required for this demo.
- Localization: English only and a single currency (US dollars).
- Branding and UI: a basic, clean branded look using the client-supplied logo and a simple palette and typography proposed by the team. The style proposal must be sent to the client for quick approval before the full UI is built, with consistent typography and colors across all screens.
- Content rights: all product images, descriptions, brand names and prices must be content owned by the client or used with rights; neutral placeholder images are allowed if real images are not ready.
- Privacy and security: the demo collects no personal data, has no accounts, and stores no user information, passwords or payment data. No card data is handled anywhere in the app.
- Quality: core flows (browse, filter, detail, add to cart, quantity change, remove, subtotal, checkout placeholder message) are covered by flutter_test widget tests and at least one integration_test run of the main journey. The app must not crash on any of these flows.
- Delivery: a demo-ready build is targeted in about 3 to 4 weeks, with no custom integrations or complex infrastructure, because budget is limited.

## Out of scope
- Real checkout, payments (including Stripe), order processing and order status handling
- User accounts, sign-in, registration and guest vs signed-in cart handling
- Backend services, API integration, live inventory and ecommerce platform integration (for example Shopify or a custom API)
- Cart persistence between app launches
- Search and sorting (only category filtering is included)
- Product reviews and ratings
- Wishlist or favorites
- Per-variant price, image or stock status; stock display and out-of-stock indicators
- Shipping, delivery options, taxes, discount codes and promotions
- Multi-currency and multi-language support
- Push notifications, analytics and marketing integrations
- Full accessibility compliance certification
- Web and desktop builds

## Assumptions
- The demo has exactly three screens: Product List (with category filters), Product Detail and Cart, within the limit of five screens.
- The sample catalog has about 24 products, roughly 6 in each of four categories: skincare, makeup, haircare and fragrance. The client supplies images, descriptions, brand names and prices; neutral placeholders are used if images are not ready.
- All prices are in US dollars. Mock data stores prices as integer cents with currency code USD.
- Size options apply to skincare and haircare products and shade options apply to makeup products, shown only where they apply. Fragrance products may show a size option or none, to be confirmed with the client's catalog data.
- Variants carry no separate price, image or stock; the selected size or shade is only recorded on the cart item.
- Adding the same product with the same variant increases quantity; a different variant creates a separate cart line.
- Minimum line quantity is 1 and a maximum per line of 99 is assumed; quantities are changed with increase and decrease controls and lines are deleted with an explicit Remove action.
- If a product has a size or shade selector, the first option may be preselected by default, otherwise the user must choose one before adding; the exact behavior is to be confirmed during UI review.
- The project convention that a cart belongs to a signed-in user is intentionally overridden for this demo: the brief excludes accounts, so there is a single anonymous in-memory cart per app session. Stock reservation, order lines and the order status flow are not implemented.
- The Checkout button is a placeholder that shows a message such as 'Checkout is coming soon. This is a demo.' and triggers no other behavior.
- The team proposes a simple palette and typography matching the client's logo and receives quick client approval before building the full UI.
- No fixed demo date exists yet; the target is a 3 to 4 week build followed by the stakeholder demo with the owner, sales and marketing leads.
- The target stack listed (NestJS, PostgreSQL, Stripe and so on) is for future phases only; this demo is Flutter-only with local or mock data and needs no backend.
