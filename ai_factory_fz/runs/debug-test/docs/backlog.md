# Delivery backlog

## Epics
- **E-01** Catalog Browse and Product Discovery (stories: US-001, US-002, US-003)
- **E-02** Shopping Cart Management (stories: US-004, US-005, US-006)

## M1: Catalog Browse, Search and Product Detail
Ship a testable first slice: users can browse products by category, search and filter, and view product details with variant selection. API returns catalog with pagination, search, filters and product details; mobile screens display products, search/filter sheet, and product detail with variant availability.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Project setup, CI/CD pipeline and health check | infra | 5 | - |  |
| WI-002 Data model, seed catalog import and database schema | backend | 5 | WI-001 |  |
| WI-003 Catalog and category API endpoints | backend | 5 | WI-002 | US-001, US-002 |
| WI-004 Product detail API endpoint | backend | 3 | WI-002 | US-003 |
| WI-005 Product List screen with category filtering and pagination | frontend | 5 | WI-003 | US-001 |
| WI-006 Search and filter sheet with sort capability | frontend | 5 | WI-005 | US-002 |
| WI-007 Product Detail screen with variant selection | frontend | 5 | WI-004 | US-003 |

## M2: Shopping Cart and Guest Checkout Readiness
Ship a testable cart slice: users can add shirts to a guest cart, view and edit cart lines, and see a subtotal. Cart persists across app restarts, reflects current prices and stock, and is ready for checkout in the next release. All 6 user stories complete, full test coverage, demo-ready build.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-008 Cart API endpoints (create, retrieve, add, update, remove items) | backend | 5 | WI-002 | US-004, US-005, US-006 |
| WI-009 Add to cart flow and cart badge | frontend | 4 | WI-007, WI-008 | US-004 |
| WI-010 Cart screen with line editing, persistence and current data | frontend | 5 | WI-009 | US-005, US-006 |
