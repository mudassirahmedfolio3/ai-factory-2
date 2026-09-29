# E-commerce Mobile Patterns

## Core user journeys

1. **Browse catalog** — categories, search, filters, product detail (images, variants, reviews).
2. **Cart** — add/update/remove items, persist cart for logged-in users, guest cart with merge on login.
3. **Checkout** — shipping address, delivery options, payment method, order review, confirmation.
4. **Account** — registration, login, profile, order history, saved addresses.
5. **Orders** — order status tracking, cancellation window, reorder.

## MVP scope guidance

- Start with catalog + cart + checkout + order confirmation.
- Defer: loyalty, subscriptions, multi-vendor, advanced promotions.
- Payment: integrate via provider SDK (Stripe, Razorpay, etc.); never store raw card data in the app.

## Mobile UX conventions

- Bottom navigation for primary tabs (Home, Categories, Cart, Account).
- Persistent cart badge with item count.
- Guest checkout with optional account creation post-purchase.
- Offline-friendly product browsing with cached catalog where possible.

## Data entities

- Product, ProductVariant, Category, Cart, CartItem, Order, OrderLine, Address, PaymentIntent.

## Compliance notes

- Display taxes and shipping before payment confirmation.
- Privacy policy and terms links on registration/checkout.
- App Store / Play Store payment rules if using in-app purchases (usually avoid for physical goods).
