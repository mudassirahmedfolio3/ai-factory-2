# Delivery backlog

## Epics
- **E-01** Design system, style approval and asset management (stories: US-006)
- **E-02** Catalog loading and product browse (stories: US-001, US-002)
- **E-03** Product detail and add to cart (stories: US-003, US-004)
- **E-04** Cart management and demo readiness (stories: US-005, US-006)

## M1: Style approval, catalog loading, Browse and Product Detail
Deliver a working Browse screen with category filter, Product Detail screen, and project foundation. Obtain business style approval and prove the catalog loads, images display with placeholders, and product details are accessible. End state: stakeholders can browse and view product details in the approved style on both iOS and Android.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Propose and get style approval (colors, typography, logo, imagery guidelines) | shared | 3 | - | US-006 |
| WI-002 Set up Flutter project, build system and dependencies | frontend | 3 | WI-001 |  |
| WI-003 Load bundled catalog JSON and define product data model | frontend | 3 | WI-002 | US-001 |
| WI-004 Build Browse screen with grid layout and image loading | frontend | 4 | WI-003 | US-001 |
| WI-005 Implement category filter on Browse screen | frontend | 3 | WI-004 | US-002 |
| WI-006 Build Product Detail screen with navigation | frontend | 3 | WI-005 | US-003 |

## M2: Cart, polish, accessibility and demo readiness
Complete the shopping demo with a fully functional in-session cart, accessibility compliance, performance verification and demo builds. End state: a polished, premium demo app running smoothly on iOS and Android that stakeholders and investors can walk through Browse, Detail, and Cart without errors.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-007 Implement quantity selector and Add to Cart logic | frontend | 4 | WI-006 | US-004 |
| WI-008 Build Cart screen with line management and totals | frontend | 4 | WI-007 | US-005 |
| WI-009 Accessibility and styling pass (contrast, text scale, touch targets) | frontend | 3 | WI-008 | US-006 |
| WI-010 Integration test and demo build verification | frontend | 4 | WI-009 | US-001, US-002, US-003, US-004, US-005 |
