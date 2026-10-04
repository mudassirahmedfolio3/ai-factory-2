# Product brief: Lighting e-commerce mobile app (MVP) — lighting-retail-mvp

Build a mobile-first lighting retail store (Android + iOS) with guest shopping, accounts, catalog, cart, checkout, orders, and an admin slice for catalog and order operations. Product domain is lighting (LED fixtures, wattage, lumens, color temperature, IP rating, etc.). MVP user journey: Open app → browse/search → product detail → select variants → add to cart → checkout → shipping & payment → place order → confirmation → track order. Customers must be able to browse, search, and filter lighting products; see product details and variants; use cart and checkout with supported payment methods; view order history and tracking. Admins must manage products, categories, variants, and inventory; view and process orders. The system must reliably handle payment errors, network failures, and duplicate submissions. Prioritize a runnable Flutter app on Android emulator plus NestJS API with OpenAPI. Use a realistic lighting seed catalog (15–30 SKUs) with the lighting-specific attributes defined for detail pages. Phase admin as API plus minimal admin UI or documented API if mobile scope is tight; do not leave the shopper path as a counter demo. Guest path must work end-to-end for demo; auth for accounts and order history.

## Target users
- Residential customers shopping for LED fixtures, bulbs, and accessories for home renovation and room upgrades
- Trade and semi-professional buyers (electricians, small contractors, interior designers) who need spec-rich listings (wattage, lumens, IP rating, dimming)
- Guest shoppers who want to complete a purchase without creating an account (MVP demo must support this path end-to-end)
- Registered customers who want order history, tracking, wishlists, and password recovery
- Internal store administrators who manage catalog, inventory, orders, promotions, and homepage content

## Business goals
- Launch an MVP that proves we can sell lighting products on mobile with a complete guest checkout path suitable for stakeholder demo
- Increase online revenue by making it easy to discover products by category, search, filters (price, brand, category, wattage, color, availability), and sorting (price, newest, popularity)
- Reduce support load by showing accurate stock, lighting specifications on product detail pages, and self-service order tracking with notifications for confirmation and shipping updates
- Operate efficiently with admin product management (add, edit, deactivate), catalog structure (categories, brands, images, specifications), variants (SKUs, prices, availability), inventory (stock quantities, out-of-stock handling), order management (view, search, manage; statuses processing, shipped, delivered), customer profiles and order history, promotions (discount coupons), and homepage banners and featured products
- Meet non-functional expectations: efficient screen and product loads; agreed minimum Android and iOS versions; secure auth, HTTPS, access controls; secure payment gateway with no raw card storage; simple, intuitive, mobile-friendly usability; network/payment/checkout failure handling; scalability for growth in products, customers, and orders; accessibility (readable text, accessible controls, contrast); data integrity (correct prices, no overselling, no duplicate orders); analytics (product views, cart adds, purchases)

## Key features
- FR-01 User Account: Register, log in, log out, reset passwords
- FR-02 Guest Access: Browse and shop without an account
- FR-03 Home: Banners, featured products, new arrivals, categories
- FR-04 Categories: Browse lighting by category and subcategory
- FR-05 Search: Search by name, SKU, brand, keywords
- FR-06 Product Listing: Images, names, prices, discounts, availability
- FR-07 Filters: Price, brand, category, wattage, color, availability
- FR-08 Sorting: Price, newest, popularity
- FR-09 Product Details: Images, descriptions, prices, specs, stock
- FR-10 Product Variants: Color, size, wattage, finish
- FR-11 Cart: Add, update qty, remove, totals
- FR-12 Wishlist: Save and remove favorites
- FR-13 Checkout: Contact, shipping address, order review
- FR-14 Payment: Secure payment (no raw card storage)
- FR-15 Order Placement: Place order + confirmation with order number
- FR-16 Order History: View past orders
- FR-17 Order Tracking: Order status and shipment info
- FR-18 Notifications: Order confirmation and shipping updates
- FR-19 Promotions: Coupon codes
- FR-20 Customer Support: Contact info and basic support channel
- AR-01 Product Management: Add, edit, deactivate products
- AR-02 Product Catalog: Categories, brands, images, specifications
- AR-03 Variants: Variants, SKUs, prices, availability
- AR-04 Inventory: Stock quantities, out-of-stock handling
- AR-05 Order Management: View, search, manage orders
- AR-06 Order Status: Processing, shipped, delivered
- AR-07 Customer Management: Profiles and order history
- AR-08 Promotions: Discount coupons
- AR-09 Content Management: Homepage banners and featured products
- Lighting-specific product attributes on detail page (show only relevant specs per product type): Product Name, SKU, Wattage, Lumens, Color Temperature, Light Type, Voltage, Dimmable, Material, Finish, Dimensions, IP Rating, Bulb Included, Installation Type. Example: Modern LED Ceiling Light, SKU CL-1001, 24W, 2400 lm, 3000K, LED, 220–240V, Dimmable Yes, Aluminum, Matte Black, 600×300 mm, IP44, Bulb Included Yes, Ceiling Mounted.
- Seed catalog: 15–30 realistic lighting SKUs covering common categories (e.g. ceiling lights, pendant, wall, outdoor, bulbs, strips) with variant combinations where commercially typical (finish, wattage, color temperature)
- Business decision — brand positioning for MVP: Single-brand storefront experience (“our store”) with multiple manufacturer brands in catalog (customers filter by brand; we are the retailer, not a marketplace with third-party sellers)
- Business decision — geography for MVP demo: One primary market with domestic shipping addresses; prices shown in local currency with tax displayed as a single line at checkout review (exact tax rules can follow standard e-commerce practice for that market)
- Business decision — out of stock: Products remain visible in listing with “Out of stock” badge; add-to-cart disabled when no stock; admins can deactivate products instead of deleting for history integrity
- Business decision — guest orders: Guest checkout collects email and phone for confirmation and support; order lookup for guests via order number plus email (registered users see full history in account)
- Business decision — customer support channel for MVP: In-app display of business hours, phone, email, and FAQ link; no live chat bot required for MVP
- Business decision — promotions: Percentage or fixed-amount coupon codes entered at checkout; one coupon per order for MVP unless we decide otherwise later

## Constraints
- NFR-01 Performance — efficient screen and product loads
- NFR-02 Compatibility — agreed minimum Android and iOS versions
- NFR-03 Security — secure auth, HTTPS, access controls
- NFR-04 Payments — secure gateway, no raw card storage
- NFR-05 Usability — simple, intuitive, mobile-friendly
- NFR-06 Reliability — network/payment/checkout failure handling
- NFR-07 Scalability — growth in products, customers, orders
- NFR-08 Accessibility — readable text, accessible controls, contrast
- NFR-09 Data Integrity — correct prices, no overselling, no duplicate orders
- NFR-10 Analytics — product views, cart adds, purchases
- Delivery: Prioritize a runnable Flutter app on Android emulator plus NestJS API with OpenAPI
- Delivery: Realistic lighting seed catalog (15–30 SKUs) with attributes above
- Delivery: Phase admin as API + minimal admin UI or documented API if mobile scope is tight; do not leave the shopper path as a counter demo
- Delivery: Guest path must work end-to-end for demo; auth for accounts and order history
- Business constraint — MVP scope: Mobile shopper experience is the priority; admin may be minimal UI but catalog and order operations must be achievable for demo via API or light admin screens
- Business constraint — payments: No storage of raw card data on our systems; use a recognized payment gateway integration pattern suitable for mobile
- Business constraint — inventory: No overselling at order placement; stock decremented or reserved according to a single clear rule implemented consistently

## Open questions
- What are the agreed minimum Android and iOS OS versions (NFR-02)?
- Which primary country/market, currency, and language(s) are in scope for launch vs demo-only?
- Which payment gateway and which payment methods (cards only, wallets, buy-now-pay-later) must be live in MVP?
- Shipping: flat rate, free over threshold, weight-based, or carrier-calculated? Which carriers and which delivery speed options?
- Returns and refunds policy for MVP — display-only text or integrated return requests in app/admin?
- Tax: single VAT/GST rate for demo vs full address-based tax calculation?
- Notifications: email only, push only, or both for order confirmation and shipping updates (FR-18)?
- Analytics: which platform or events schema (NFR-10) — and what is acceptable for MVP without privacy review delay?
- Admin access: single admin role for MVP or separate roles (catalog vs orders vs super-admin)?
- Product content: who supplies photography and long descriptions for seed SKUs — stock placeholders acceptable for MVP?
- Wishlist (FR-12): require login to persist wishlist, or allow guest wishlist on device only?
- Popularity sort (FR-08): defined by sales volume, views, or manual merchandising flag for MVP?
- Categories taxonomy: final top-level and subcategory list for lighting (e.g. indoor/outdoor, room type, fixture type) — need merchandising sign-off
- International: ship cross-border in MVP or domestic only?
- Legal: terms of service, privacy policy, and cookie/consent requirements for target market — who provides copy?
- Coupon rules (FR-19 / AR-08): stackable with sale prices, expiry dates, minimum order value, single-use per customer?
- Order tracking (FR-17): manual status updates by admin only, or carrier tracking number integration in MVP?
- Accessibility (NFR-08): target compliance level (e.g. WCAG 2.1 AA) for MVP vs best-effort?
- iOS delivery timing: Android emulator first is agreed — is iOS build/test required before MVP sign-off or parallel phase 2?
