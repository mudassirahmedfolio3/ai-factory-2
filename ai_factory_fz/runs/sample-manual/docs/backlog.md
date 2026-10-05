<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. Delete this folder when you have a real run. -->
# Backlog: ShopEase Mini

## Epics
- E-01 Catalog: browse products and read product details
- E-02 Cart: add products, see the cart and its total

## Work items

| Id | Epic | Component | Title | Points | Stories | Depends on |
|---|---|---|---|---|---|---|
| WI-001 | E-01 | backend | Products API: list and get one, with seed data | 3 | US-001, US-002 | - |
| WI-002 | E-02 | backend | Cart API: anonymous cart, add item, change quantity, get cart with total | 4 | US-003, US-004 | WI-001 |
| WI-003 | E-01 | frontend | Product list screen with loading and empty states | 3 | US-001 | WI-001 |
| WI-004 | E-01 | frontend | Product detail screen with error state | 2 | US-002 | WI-003 |
| WI-005 | E-02 | frontend | Add to cart from product detail | 2 | US-003 | WI-002, WI-004 |
| WI-006 | E-02 | frontend | Cart screen with quantities, totals and empty state | 3 | US-004 | WI-002, WI-005 |

## Milestones

### M1: Browse the catalog
Ends in: a shopper can open the app, see the product list and open a product's details.
Work items: WI-001, WI-003, WI-004

### M2: Cart
Ends in: a shopper can add a product to the cart, change quantities and see the correct total.
Work items: WI-002, WI-005, WI-006

## Story coverage
- US-001: WI-001, WI-003
- US-002: WI-001, WI-004
- US-003: WI-002, WI-005
- US-004: WI-002, WI-006
