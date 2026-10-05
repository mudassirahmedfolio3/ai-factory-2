# Delivery backlog

## Epics
- **E-01** Browse Lighting Products (stories: US-001)
- **E-02** View Product Details and Variants (stories: US-002)
- **E-03** In-Memory Shopping Cart (stories: US-003)

## M1: Speed Demo MVP Complete
Deliver a runnable Android Flutter app with product browse, product detail, and optional in-memory cart. All must-have user stories (US-001 and US-002) are complete and tested. Optional cart (US-003) is included if it does not delay core delivery. The app launches on an Android emulator within 3 seconds, loads products from a bundled mock catalog, supports variant switching with real-time price and SKU updates, displays prices as integer cents formatted in USD, and provides a simple in-memory cart with tax and shipping totals calculated using integer arithmetic. No backend API, authentication, or payment processing is required. Style tokens are chosen by the delivery team without approval delays.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project structure with Riverpod and go_router | frontend | 3 | - | US-001 |
| WI-002 Create mock catalog data model and bundled asset | shared | 3 | WI-001 | US-001, US-002 |
| WI-003 Build product list screen with lazy-loaded images and scroll performance | frontend | 4 | WI-001, WI-002 | US-001 |
| WI-004 Build product detail screen with variant switching and specifications | frontend | 4 | WI-001, WI-002, WI-003 | US-002 |
| WI-005 Implement in-memory cart with totals calculation and tax/shipping logic | frontend | 5 | WI-001, WI-004 | US-003 |
