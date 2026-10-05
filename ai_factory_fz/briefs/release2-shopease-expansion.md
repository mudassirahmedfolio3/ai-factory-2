
# Release 2 — expand ShopEase (same run, more client-ready functionality)

Continue on the existing codebase. M1 guest catalog + M2 API integration are the baseline. This release adds **shopper-facing depth** and **richer demo narrative** (still demo-safe; mock payment is OK).

## Priority features (implement as new work items / milestones in this release)

1. **Accounts (FR-01 lite)** — Register, log in, log out; secure token storage; optional password reset stub.
2. **Guest + signed-in (FR-02)** — Keep guest browse/cart; signed-in users persist cart or order history in session/API as feasible.
3. **Home (FR-03)** — Home route with banners, featured products, new arrivals, category entry (not only product list).
4. **Search & filters (FR-05–FR-08)** — Extend list: keyword search, sort (price, newest), filters already started (price, category) plus brand/availability where seed data supports it.
5. **Wishlist (FR-12)** — Save/remove favorites (local or API-backed).
6. **Checkout flow (FR-13–FR-15)** — Contact + shipping address + order review; place order with confirmation screen and order number (mock payment / PaymentIntent stub acceptable).
7. **Order history & tracking (FR-16–FR-17)** — List past orders and show status (processing → shipped → delivered).
8. **Promotions (FR-19)** — Apply coupon code at checkout (validate against seed promos).
9. **Support (FR-20)** — In-app contact/support screen with clear contact channel.
10. **Backend** — Extend NestJS OpenAPI + Prisma only as needed for orders, auth slice, coupons; keep analyze/tests green.

## Quality bar

- Flutter app must still **run on Android emulator** (not counter template).
- `flutter analyze` and `flutter test` pass; server tests pass for new endpoints.
- Update docs/PRD backlog section to reflect Release 2 scope; QA one round minimum.

## Out of scope for this release pass

- Full admin panel (AR-01–AR-09) — document as follow-up unless time allows a minimal read-only admin API.
- Production push notifications (FR-18) — log/mock only.
- Real payment processor keys — use test/mock gateway only.
