# Delivery backlog

## Epics
- **E-01** Mobile Speed Demo - Browse, Detail, Cart (stories: US-001, US-002, US-003)

## M1: Mobile Speed Demo - Browse, Detail, Cart
Deliver a small runnable Flutter MVP running on Android emulator with a local mock catalogue, product list screen, product detail screen, optional in-memory cart, and all must-have stories (US-001, US-002) plus could-have cart (US-003) working end-to-end with no backend API, no authentication, and no payments. The app launches within 3 seconds, all prices are displayed as VAT-inclusive GBP from integer minor units, and the complete shopping journey is testable by the product team on an emulator.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project structure and mock catalogue data | frontend | 3 | - | US-001, US-002, US-003 |
| WI-002 Build product list screen and mock data provider | frontend | 3 | WI-001 | US-001 |
| WI-003 Build product detail screen with variant selection and stock status | frontend | 3 | WI-002 | US-002 |
| WI-004 Implement in-memory cart state management and cart screen | frontend | 4 | WI-003 | US-003 |
| WI-005 Apply theme tokens, finalize accessibility and test | frontend | 3 | WI-002, WI-003, WI-004 | US-001, US-002, US-003 |
