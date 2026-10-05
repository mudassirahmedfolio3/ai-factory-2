# Delivery backlog

## Epics
- **E-01** Browse beauty products in a grid (stories: US-001)
- **E-02** View product detail (stories: US-002)
- **E-03** Add to cart with in-memory count (stories: US-003)

## M1: Flutter Beauty Shop Speed Demo
Deliver a working Flutter MVP that runs on Android emulator in under 10 minutes with no backend, auth or payments. Internal team can see the core browse-to-detail-to-cart flow with 8 hardcoded beauty products, validate the experience, and decide what to build next. Developers have a clear, extensible base for future milestones.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Scaffold Flutter project with basic folder structure | frontend | 2 | - | US-001 |
| WI-002 Create hardcoded product data model and local catalog | frontend | 2 | WI-001 | US-001, US-002 |
| WI-003 Build browse screen with product grid and navigation | frontend | 3 | WI-002 | US-001 |
| WI-004 Build product detail screen with back navigation | frontend | 2 | WI-003 | US-002 |
| WI-005 Implement in-memory cart with count badge and add-to-cart button | frontend | 3 | WI-004 | US-003 |
