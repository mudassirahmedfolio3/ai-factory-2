# Delivery plan (work breakdown)

Total: 5 work items, 20 points. Critical path (16 points): WI-001 → WI-003 → WI-004 → WI-005

## Epics
- **E-01** PulsePhones catalog browse and detail (stories: US-001, US-002)
- **E-02** Session in-memory cart path (stories: US-003)

## Estimation review
Developers re-estimated every item: 4 changed from the PM's draft, 0 big disagreements reconciled by the PM (highest estimate risk).

## M1: Browse & Detail Demo (20 pts)
Runnable PulsePhones Flutter Android MVP on emulator from local seed (list, detail, optional in-memory cart) plus OpenAPI/Prisma stubs for getHealth, listProducts, and getProductById covering the full solution schema—no auth, payments, or checkout in this demo.

| Item | Feature | Component | Pts | Risk/Conf. | Builds | Depends on | Why this size |
|---|---|---|---|---|---|---|---|
| WI-001 OpenAPI contract, Prisma schema, and Nest catalog stubs | Catalog API | backend | 5 (PM 5, dev 5) | medium/high | getHealth, listProducts, getProductById; User, RefreshToken, Address, Category, Product, ProductVariant, Cart, CartItem, Order, OrderItem, Payment | - | Three stub operations plus full Prisma entity set and OpenAPI contract scaffolding. | backend_developer: OpenAPI for three ops, full Prisma schema with eleven related models, Nest stubs across health/catalog plus deferred module shells, docker-compose Postgres, and Jest/Supertest to keep the build green is about one focused day.; concerns: OpenAPI response shapes must match the Flutter M1 catalog mock or M2 client generation will break; deferred modules still need correct Prisma relations and enums now; health e2e needs Postgres available when probes run. |
| WI-002 Flutter scaffold, PulsePhones theme, and routing | App foundation | frontend | 4 (PM 3, dev 4) | low/high | - | - | Standard Flutter scaffold plus Riverpod/go_router wiring and theme tokens only. | frontend_developer: Flutter 3.x Android scaffold, Riverpod/go_router, PulsePhones tokens, debug cleartext for 10.0.2.2, and offline launch green on emulator—more than bare wiring.; concerns: Offline M1 still needs a deliberate no-live-HTTP path (stubs/flags) so debug builds never dial the network; android/app/src/debug network-security-config must not leak into release. |
| WI-003 Local catalog seed, ProductListScreen, and ProductDetailScreen | Catalog screens | frontend | 6 (PM 5, dev 6) | low/high | listProducts, getProductById; Category, Product, ProductVariant; SCR-01, SCR-02 | WI-001, WI-002 | Seed JSON, cents+USD models, two screens with AsyncNotifiers and branding/ratings. | frontend_developer: freezed/json_serializable Category/Product/ProductVariant (cents), 12–20-seed catalog.json, LocalCatalogDataSource/repository, two AsyncNotifiers, and SCR-01/SCR-02 with loading/empty/error plus branding/ratings/specs.; concerns: Depends on WI-001 but M1 is local-only—clarify seed JSON shape vs listProducts/getProductById so M2 swap to generated CatalogApi stays clean; image/placeholder assets and build_runner CI are easy to under-scope. |
| WI-004 In-memory CartNotifier and CartScreen | Cart screen | frontend | 2 (PM 3, dev 2) | low/high | Cart, CartItem; SCR-02, SCR-03 | WI-003 | In-memory quantity CRUD and one cart screen wired from detail. | frontend_developer: Session CartNotifier with line snapshots, add-from-detail, and SCR-03 quantity CRUD/empty state—straightforward once catalog models exist.; concerns: Provider scope must keep cart across go_router list↔detail↔cart; no persistence is fine for M1 but document clear-on-restart for demo expectations. |
| WI-005 Browse–detail–cart Flutter tests | M1 verification | frontend | 3 (PM 2, dev 3) | medium/medium | SCR-01, SCR-02, SCR-03 | WI-003, WI-004 | Widget tests over local seed and in-memory cart; no device flakiness in M1. | frontend_developer: Widget (and light integration) coverage for cents→USD list, detail round-trip preserving catalog state, and in-memory cart add/qty/remove—Riverpod overrides + go_router harness drive the effort.; concerns: go_router/Riverpod pumpAndSettle flakiness and integration_test Android emulator setup often exceed a 2-pt slice; need shared test fixtures over the seed catalog. |
