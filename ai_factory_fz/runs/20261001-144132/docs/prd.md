# RetailHub Mobile Shopping App – Speed Demo MVP

A minimal Flutter mobile application enabling customers to browse and discover products through an intuitive product catalog with search and filtering. This MVP focuses on the core discovery and product detail experience to validate the market and demonstrate core functionality. No authentication, payment processing, or checkout logic is included in this release. The app uses a local mock product catalog embedded in Flutter to enable immediate testing on emulators without backend infrastructure overhead.

## Personas
### Mobile-First Shopper
A busy professional aged 25–45 who prefers shopping on their phone during commute or lunch breaks. Values speed, discovery, and recommendations. Rarely carries a laptop and expects a seamless, touch-optimized experience.
- Browse products quickly on mobile without friction
- Discover new items matching my interests
- See clear pricing and product information at a glance

### In-Store Customer Moving Online
A 35–60 year old existing retail customer exploring the new mobile app for the first time. Familiar with the product range but wants the convenience of browsing and purchasing from home or anywhere.
- Navigate the app intuitively with minimal learning curve
- Find products they remember from physical stores
- Trust that app pricing matches store prices

### New Customer Discovery
A 18–35 year old discovering the brand for the first time through app recommendations, search results, or social sharing. Seeks a first impression of quality, range, and brand trustworthiness.
- Quickly understand what the store offers
- Search for specific products easily
- See customer reviews and ratings to build confidence

## User stories
### US-001 Browse product catalog with category filtering (must)
As a mobile-first shopper, I want to view a list of products organized by category with the ability to filter and search, so that I can quickly discover products that match my interests without scrolling through thousands of irrelevant items.

- **Given** I open the app for the first time **when** the product list screen loads **then** I see at least 10 products displayed in a grid or list format with product image, name, price in the correct currency, and a star rating
- **Given** products are displayed on the catalog screen **when** I apply a category filter (e.g., Electronics, Clothing, Home) **then** the list updates to show only products in that category within 1 second
- **Given** I am viewing the product catalog **when** I enter a search term in the search box **then** the product list filters to show only products whose name or description contains that search term, with results appearing within 500ms

### US-002 View detailed product information (must)
As a mobile-first shopper, I want to tap on a product and see full details including description, images, price, stock status, and customer reviews, so that I can make an informed decision about whether to purchase without leaving the app.

- **Given** I am viewing the product catalog **when** I tap on a product tile **then** the app navigates to a product detail screen showing the product image, full name, price (in correct currency code), complete description, stock status (in stock / out of stock), and at least 3 customer review snippets with ratings
- **Given** I am on a product detail screen **when** the product has multiple images available **then** I can swipe horizontally through at least 2 images
- **Given** a product is out of stock **when** I view its detail page **then** an 'Out of Stock' badge is clearly visible and the product cannot be added to cart

### US-003 Add product to cart and view cart summary (must)
As a mobile-first shopper, I want to add products to a shopping cart and see a summary of my selections before checking out, so that I can review my choices and proceed to payment when ready.

- **Given** I am on a product detail screen for an in-stock product **when** I tap the 'Add to Cart' button **then** the product is added to cart, a brief confirmation message appears (e.g., 'Added to cart'), and a cart badge or counter increments by 1
- **Given** I have added one or more products to my cart **when** I tap the cart icon or cart menu option **then** I see a cart summary screen listing all items with product name, unit price, quantity, and a calculated subtotal
- **Given** I am viewing the cart summary **when** I remove a product from the cart by tapping a remove or delete button **then** the item is removed immediately, the subtotal updates, and the cart count decrements

## Non-functional requirements
- Performance: Product list must load and render within 2 seconds on a 4G connection. Search and category filtering must respond within 500ms. Product detail page must load within 1 second.
- Platforms: App must run on iOS 13+ and Android 10+ and be tested on at least one iOS device/emulator and one Android device/emulator.
- Accessibility: All interactive elements must have a minimum touch target size of 44×44 points (iOS) or 48 dp (Android). Text must have sufficient color contrast (WCAG AA standard). Screen reader support for essential UI elements (product name, price, buttons) is required.
- Storage: Cart data must persist in local memory for the duration of the app session (in-memory only for this MVP; no persistent local database required).
- Offline: The app must gracefully handle network unavailability by displaying cached product data or a 'No Connection' message without crashing.
- Data Privacy: The app must not collect, store, or transmit personally identifiable information (name, email, address, payment data). No analytics or crash reporting should transmit user data to external services during the MVP phase.
- Code Quality: All user-facing code must be covered by unit and widget tests with a minimum of 70% code coverage for the navigation and product list UI layers. The codebase must follow Dart style guide conventions and pass linting with zero critical warnings.
- Security: No hardcoded API keys, credentials, or sensitive configuration in the codebase. Mock product data must be generated from a local JSON file or Dart const structure only.

## Out of scope
- User account creation and authentication (no login/sign-up flow)
- Payment processing and checkout (no Stripe integration, no payment intent creation)
- Order management and order history (no order status tracking or order detail screens)
- Returns and refunds process (not applicable without checkout)
- Shipping and delivery integration (no carrier APIs or shipping cost calculations)
- Loyalty points system (deferred to v2)
- Push notifications and promotional messaging (deferred to v2)
- Customer reviews submission or moderation (reviews are mock data only)
- Wishlist functionality (deferred to v2)
- Live chat or in-app customer support (deferred to v2)
- Real-time inventory synchronization with backend (inventory is static mock data)
- User profile, saved addresses, or payment method storage (deferred to v2)
- Guest checkout or account creation workflows (deferred to v2)
- Multi-language support (English only for MVP)

## Assumptions
- The mock product catalog contains at least 15–20 representative products across 3–4 categories (e.g., Electronics, Clothing, Home & Garden, Sports) to enable meaningful testing of search, filtering, and detail screens.
- Customer review data is hardcoded or loaded from a local JSON fixture and represents realistic ratings (1–5 stars) and review snippets.
- The product price data is represented as integer minor units (cents) with an ISO 4217 currency code (e.g., USD, EUR) to prepare for future payment integration, but the MVP display layer may show formatted currency strings.
- Cart state persists in-memory only during app lifecycle; closing and reopening the app will reset the cart. No persistence to device storage is required for this MVP.
- The app assumes iOS 13+ and Android 10+ as minimum OS versions; no testing is required for older versions.
- No backend API calls are required for the MVP. All product and review data is embedded in the Flutter app.
- No analytics, crash reporting, or user tracking is enabled in the MVP release.
- The app is single-user (no multi-user support) and runs in isolation on the device.
