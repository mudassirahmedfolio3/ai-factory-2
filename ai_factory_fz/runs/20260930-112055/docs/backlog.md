# Delivery backlog

## Epics
- **E-01** Product Browsing (stories: US-001, US-002)
- **E-02** Product Details and Cart Management (stories: US-003, US-004, US-005, US-006)

## M1: Foundation and Browsing
Flutter project setup, mock catalog ready, Product List and filter working and tested. Testable slice: user can launch app, view all 24 products, filter by category and navigate to detail screen.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project, routing and navigation structure | frontend | 3 | - | US-001 |
| WI-002 Build mock product catalog with 24 products in four categories | shared | 2 | - | US-001, US-002 |
| WI-003 Design and approve UI theme and style guide | frontend | 2 | - | US-001 |
| WI-004 Build Product List screen with scrollable grid, product cards and placeholder images | frontend | 3 | WI-001, WI-002, WI-003 | US-001 |
| WI-005 Implement category filter controls and filtering logic | frontend | 2 | WI-004 | US-002 |

## M2: Cart and Demo Ready
Product Detail, cart state management and Cart screen complete with all controls and subtotal. Checkout placeholder in place. Full widget and integration tests passing. Testable slice: user can browse, filter, select product variant, add to cart, modify quantities, remove items, and see correct subtotal. Checkout shows placeholder message. Demo-ready build for stakeholder review on iOS and Android.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-006 Build Product Detail screen with variant selectors and Add to Cart button | frontend | 4 | WI-001, WI-002, WI-004 | US-003, US-004 |
| WI-007 Implement cart state management with Riverpod | frontend | 3 | WI-002 | US-004, US-005 |
| WI-008 Build Cart screen with item list, quantity controls and subtotal display | frontend | 3 | WI-006, WI-007 | US-005, US-006 |
| WI-009 Implement Checkout placeholder button with 'coming soon' message | frontend | 1 | WI-008 | US-006 |
| WI-010 Write widget and integration tests covering core flows | shared | 4 | WI-004, WI-005, WI-006, WI-008 | US-001, US-002, US-003, US-004, US-005, US-006 |
