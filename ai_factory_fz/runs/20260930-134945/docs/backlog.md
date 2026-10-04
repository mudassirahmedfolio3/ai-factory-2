# Delivery backlog

## Epics
- **E-01** Browse Lighting Products (stories: US-001)
- **E-02** View Product Details with Specifications (stories: US-002)
- **E-03** In-Memory Shopping Cart (stories: US-003)

## M1: Browse-to-Cart Journey Speed Demo
Deliver a runnable Flutter MVP on Android emulator showing the complete guest shopping journey: browse product list, view product detail with lighting specifications, add to in-memory cart and view cart with price computation, all offline with mock catalog. App launches within 3 seconds, list scrolls smoothly, prices computed and displayed correctly in GBP pence, and end-to-end journey testable on emulator.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project structure with Riverpod, go_router, freezed and testing | frontend | 3 | - | US-001, US-002, US-003 |
| WI-002 Create mock product catalog asset and data model | frontend | 3 | WI-001 | US-001 |
| WI-003 Implement Product List screen with lazy image loading, price formatting and stock status | frontend | 4 | WI-002 | US-001 |
| WI-004 Implement Product Detail screen with specifications and quantity selector | frontend | 4 | WI-003 | US-002 |
| WI-005 Implement in-memory Cart screen and state management with price arithmetic | frontend | 4 | WI-004 | US-003 |
