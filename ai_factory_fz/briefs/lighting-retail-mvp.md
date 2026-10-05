# Lighting e-commerce mobile app (MVP)

Build a **mobile-first lighting retail** store (Android + iOS) with guest shopping, accounts, catalog, cart, checkout, orders, and an **admin** slice for catalog and order operations. Product domain is **lighting** (LED fixtures, wattage, lumens, color temperature, IP rating, etc.).

## 1. Functional requirements

| ID | Module | Requirement |
|----|--------|-------------|
| FR-01 | User Account | Register, log in, log out, reset passwords |
| FR-02 | Guest Access | Browse and shop without an account |
| FR-03 | Home | Banners, featured products, new arrivals, categories |
| FR-04 | Categories | Browse lighting by category and subcategory |
| FR-05 | Search | Search by name, SKU, brand, keywords |
| FR-06 | Product Listing | Images, names, prices, discounts, availability |
| FR-07 | Filters | Price, brand, category, wattage, color, availability |
| FR-08 | Sorting | Price, newest, popularity |
| FR-09 | Product Details | Images, descriptions, prices, specs, stock |
| FR-10 | Product Variants | Color, size, wattage, finish |
| FR-11 | Cart | Add, update qty, remove, totals |
| FR-12 | Wishlist | Save and remove favorites |
| FR-13 | Checkout | Contact, shipping address, order review |
| FR-14 | Payment | Secure payment (no raw card storage) |
| FR-15 | Order Placement | Place order + confirmation with order number |
| FR-16 | Order History | View past orders |
| FR-17 | Order Tracking | Order status and shipment info |
| FR-18 | Notifications | Order confirmation and shipping updates |
| FR-19 | Promotions | Coupon codes |
| FR-20 | Customer Support | Contact info and basic support channel |

## 2. Admin requirements

| ID | Module | Requirement |
|----|--------|-------------|
| AR-01 | Product Management | Add, edit, deactivate products |
| AR-02 | Product Catalog | Categories, brands, images, specifications |
| AR-03 | Variants | Variants, SKUs, prices, availability |
| AR-04 | Inventory | Stock quantities, out-of-stock handling |
| AR-05 | Order Management | View, search, manage orders |
| AR-06 | Order Status | Processing, shipped, delivered |
| AR-07 | Customer Management | Profiles and order history |
| AR-08 | Promotions | Discount coupons |
| AR-09 | Content Management | Homepage banners and featured products |

## 3. Non-functional requirements

NFR-01 Performance — efficient screen and product loads  
NFR-02 Compatibility — agreed minimum Android and iOS versions  
NFR-03 Security — secure auth, HTTPS, access controls  
NFR-04 Payments — secure gateway, no raw card storage  
NFR-05 Usability — simple, intuitive, mobile-friendly  
NFR-06 Reliability — network/payment/checkout failure handling  
NFR-07 Scalability — growth in products, customers, orders  
NFR-08 Accessibility — readable text, accessible controls, contrast  
NFR-09 Data Integrity — correct prices, no overselling, no duplicate orders  
NFR-10 Analytics — product views, cart adds, purchases  

## 4. Lighting-specific product attributes (detail page)

Product Name, SKU, Wattage, Lumens, Color Temperature, Light Type, Voltage, Dimmable, Material, Finish, Dimensions, IP Rating, Bulb Included, Installation Type — show only relevant specs per product type.

Example: Modern LED Ceiling Light, SKU CL-1001, 24W, 2400 lm, 3000K, LED, 220–240V, Dimmable Yes, Aluminum, Matte Black, 600×300 mm, IP44, Bulb Included Yes, Ceiling Mounted.

## 5. MVP user journey

Open app → browse/search → product detail → select variants → add to cart → checkout → shipping & payment → place order → confirmation → track order.

## 6. MVP completion criteria

- Customers browse, search, filter lighting products  
- Product details and variants  
- Cart and checkout with supported payment methods  
- Order history and tracking  
- Admins manage products, categories, variants, inventory  
- Admins view and process orders  
- Reliable handling of payment errors, network failures, duplicate submissions  

## Delivery notes for AI Factory

- Prioritize a **runnable Flutter app on Android emulator** plus **NestJS API** with OpenAPI.  
- Use **realistic lighting seed catalog** (15–30 SKUs) with attributes above.  
- Phase admin as API + minimal admin UI or documented API if mobile scope is tight; do not leave the shopper path as a counter demo.  
- Guest path must work end-to-end for demo; auth for accounts and order history.
