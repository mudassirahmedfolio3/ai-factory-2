# Delivery backlog

## Epics
- **E-01** Catalogue API and Product Data (stories: US-001, US-002, US-003)
- **E-02** Mobile App Browse, Search and Product Detail (stories: US-001, US-002, US-003)
- **E-03** Mobile App Cart and Order Request (stories: US-004, US-005, US-006)

## M1: Backend Catalogue API
Deliver a working NestJS backend with PostgreSQL, health check, full product catalogue API (categories, products with search and category filters, product detail with variants), seeded product data, and OpenAPI documentation. Enable mobile teams to build screens and integration tests against stable contract.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Backend: Set up NestJS, Prisma, PostgreSQL and Docker | infra | 3 | - |  |
| WI-002 Backend: Implement health check and product catalogue API | backend | 5 | WI-001 | US-001, US-002, US-003 |
| WI-003 Backend: Define data model, seed catalogue and enable staff updates | backend | 4 | WI-001 | US-001, US-002, US-003 |

## M2: Mobile App: Browse, Search, Detail, Cart and Order Request
Ship a fully functional Flutter app with product browsing (catalogue and search screens), product detail with variant selection, on-device cart with persistence, cart line editing, price and stock refresh when online, order request feature (WhatsApp/email fallback), analytics, image caching, accessibility and end-to-end tests. Ready for iOS and Android beta release to validate mobile demand and cart-add rate metrics.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-004 Mobile: Project setup, architecture, dependencies and API client | frontend | 4 | WI-002 | US-001, US-002, US-003 |
| WI-005 Mobile: Build Catalogue screen with category filter and loading states | frontend | 4 | WI-004 | US-001 |
| WI-006 Mobile: Build Search screen and Product Detail with variant selection | frontend | 5 | WI-005 | US-002, US-003 |
| WI-007 Mobile: Implement local cart storage, add to cart and cart persistence | frontend | 4 | WI-006 | US-004, US-005 |
| WI-008 Mobile: Build Cart screen, refresh prices online and order request feature | frontend | 5 | WI-007 | US-005, US-006 |
| WI-009 Mobile: Analytics, image caching, accessibility and Privacy screen | frontend | 4 | WI-008 | US-001, US-002, US-003, US-004, US-005, US-006 |
| WI-010 Mobile and Backend: End-to-end testing and launch readiness | shared | 4 | WI-008, WI-009 | US-001, US-003, US-004, US-005, US-006 |
