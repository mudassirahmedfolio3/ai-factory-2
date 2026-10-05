# Delivery backlog

## Epics
- **E-01** Browse Product List (M1 Speed Demo) (stories: US-001)
- **E-02** View Product Detail (M1 Speed Demo) (stories: US-002)
- **E-03** Simple In-Memory Cart (M1 Speed Demo) (stories: US-003)

## M1: ShopEase M1 Speed Demo
Deliver a runnable Flutter app on Android emulator showing product list, product detail, and optional in-memory cart, using only a bundled local mock catalog. Cold start to first rendered product list in under 3 seconds. All prices in integer cents USD, no hard-coded symbols. At least 3 flutter_test tests covering price formatting, catalog loading and cart subtotal. No authentication, payments, backend API or network required. App builds with no analyzer errors.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project structure, routing and style tokens | frontend | 3 | - | US-001 |
| WI-002 Create mock product catalog with variants, prices and stock | frontend | 2 | WI-001 | US-001 |
| WI-003 Build product list screen with scrolling and formatting | frontend | 3 | WI-002 | US-001, US-002 |
| WI-004 Build product detail screen with variant selection and stock status | frontend | 3 | WI-003 | US-002 |
| WI-005 Implement in-memory cart with item management and subtotal | frontend | 3 | WI-004 | US-003 |
