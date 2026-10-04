# Delivery backlog

## Epics
- **E-01** Browse and Product Detail – Flutter MVP (stories: US-001, US-002, US-003)

## M1: Browse and Detail MVP – Runnable on Emulator
Deliver a runnable Flutter app on Android emulator with product list and detail screens backed by a local mock catalogue, smooth scrolling, accessible UI, and optional in-memory cart. The app must start within 3 seconds, handle out-of-stock products, and require no backend, authentication or payments. Team and stakeholders can demo the core browse-to-detail journey end to end.

| Item | Component | Pts | Depends on | Stories |
|---|---|---|---|---|
| WI-001 Set up Flutter project, mock catalogue repository and project structure | frontend | 3 | - | US-001, US-002 |
| WI-002 Build product list screen and repository integration | frontend | 3 | WI-001 | US-001 |
| WI-003 Build product detail screen with navigation | frontend | 3 | WI-001, WI-002 | US-002 |
| WI-004 Implement in-memory cart state and cart screen (optional) | frontend | 3 | WI-003 | US-003 |
| WI-005 Polish, performance testing and release readiness | frontend | 2 | WI-002, WI-003, WI-004 | US-001, US-002, US-003 |
