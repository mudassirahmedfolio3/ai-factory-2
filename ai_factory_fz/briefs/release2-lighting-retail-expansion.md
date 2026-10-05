# Release 2 — lighting-retail MVP expansion (same run, Pass 2)

Continue on the existing **Lumen / lighting-retail** codebase in this run workspace. **Pass 1 (M1 + M2) is complete**: Flutter guest catalog with local/API catalog, NestJS `/api/v1` health + catalog OpenAPI, Dart client with fallback. Do **not** replan or duplicate Pass 1 work items **WI-001 through WI-012**. Treat that baseline as shipped unless Release 2 needs a small delta fix.

Plan exactly **one new milestone M3** named **"Release 2 — shopper depth & production catalog"** with **new work items only**, continuing IDs from **WI-013** upward.

## Shopper features (UK lighting retail — align with original FRs where feasible)

1. **Accounts (FR-01)** — Register, log in, log out; secure token storage; password-reset stub (email deep link or in-app “check your email” demo).
2. **Guest + signed-in (FR-02)** — Keep guest browse/cart/checkout path; signed-in users get persisted cart merge on login and order history.
3. **Home (FR-03)** — Banners, featured products, new arrivals, category entry (API-backed when health OK).
4. **Search & discovery (FR-04–FR-08)** — Keyword search (name, SKU, brand); sort (price, newest, popularity); filters including brand, availability, wattage/finish where seed supports.
5. **Wishlist (FR-12)** — Save/remove favorites; API sync when signed in.
6. **Checkout (FR-13–FR-15)** — Contact, UK shipping address, order review, mock payment (no raw card storage), order confirmation with order number.
7. **Orders (FR-16–FR-17)** — Order history and status (processing → shipped → delivered).
8. **Promotions (FR-19)** — Coupon code at checkout against seed promos.
9. **Support (FR-20)** — In-app support/contact screen (hours, phone, email, FAQ link).
10. **Backend** — Extend Prisma seed, NestJS modules, and OpenAPI for auth, orders, coupons, home merchandising as needed; keep Jest/e2e green.

## Real product imagery (required for final MVP demo)

Pass 1 used placeholder or generic catalog imagery. **Release 2 must show real lighting product photos** in list, detail, home carousels, and cart line items.

**Primary reference catalog (demo-safe):**

- Browse and extract product names, categories, and **image URLs** from  
  **https://stanpro2.folio3.site/search**  
  and linked product detail pages on the same site (Stanpro-style step lights, indoor, emergency, etc.).

**Implementation rules:**

- Target **18–30 SKUs** with **at least one real photo each** (prefer 2–3 angles where available).
- **Download** images into the run workspace (e.g. `app/assets/catalog/images/` and/or server seed static paths under `apps/api/`) — do **not** rely on hotlinking alone for the demo build; bundled assets must work offline on the emulator.
- Record provenance in **`docs/IMAGE_SOURCES.md`**: product SKU/name, source page URL, image URL, retrieval date. Demo/staging use only; not for production redistribution without license review.
- If a stanpro page lacks a usable image, supplement from other **public manufacturer or retailer pages** for the same product type (document each source).
- Update **`assets/data/catalog.json`**, Prisma seed, and API mappers so **the same image paths/URLs** appear in Flutter and NestJS responses.
- Product copy (wattage, lumens, IP, color temp) should stay **consistent with lighting specs** already modeled; align titles with sourced products where possible.

## Quality bar

- Flutter: **`flutter analyze`** and **`flutter test`** green; guest path still works end-to-end on Android emulator.
- Server: unit + Supertest e2e for new endpoints; OpenAPI parity with `docs/openapi.yaml`.
- One **QA round on M3** before calling Release 2 done.
- Update PRD/backlog docs to reflect M3 scope.

## Out of scope for this pass

- Full admin panel UI (AR-01–AR-09) — optional read-only admin API docs only if time remains.
- Production payment keys, push notifications (FR-18 mock/log only).
- iOS store submission.
