# Delivery backlog

## Epics
- **E-01** User Authentication (Sign In & Register) (stories: US-001)
- **E-02** Product Catalog & Search (stories: US-002, US-003)
- **E-03** Product Detail & Variants (stories: US-004)
- **E-04** Shopping Cart (stories: US-005, US-006)

## M1: User Authentication
End-to-end user registration, sign-in, and session persistence. Verify user can register with email/password, sign in, maintain session across app close/reopen, and see auth errors.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Backend: User registration and sign-in with JWT auth | backend | 5 | - | US-001 |
| WI-002 Frontend: Sign in and register screens with form validation | frontend | 5 | WI-001 | US-001 |

## M2: Product Catalog, Search, Cart and Complete Core Flow
Verify user can browse products by category/subcategory, search by keyword, view product details with photos and variants, add items to cart, view cart with pricing calculations, and edit cart quantities. Confirm all 10 API operations work and core journey is testable end-to-end.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-003 Backend: Product catalog endpoints (list by category, pagination, detail) | backend | 5 | - | US-002, US-004 |
| WI-004 Backend: Product search endpoint | backend | 3 | WI-003 | US-003 |
| WI-005 Frontend: Category browse, product list, and search screens | frontend | 5 | WI-003, WI-004 | US-002, US-003 |
| WI-006 Backend: Product detail with variants and stock status | backend | 2 | WI-003 | US-004 |
| WI-007 Frontend: Product detail screen with photo gallery and variant selection | frontend | 5 | WI-006, WI-002 | US-004 |
| WI-008 Backend: Cart endpoints (GET, POST add/update, DELETE remove) | backend | 5 | WI-001, WI-003 | US-005, US-006 |
| WI-009 Frontend: Add to cart flow with auth redirect | frontend | 4 | WI-008, WI-007, WI-002 | US-005 |
| WI-010 Frontend: Cart screen view and edit with live summary | frontend | 5 | WI-008, WI-002 | US-006 |
