# Release 2 (M3) sign-off checklist — WI-026

Use this checklist after one structured M3 QA round (US-001–US-014, SCR-01–SCR-14). All automated gates must be green before staging promotion; production requires manual **Deploy** workflow approval.

## Automated gates (CI)

- [ ] `.github/workflows/ci.yml` — NestJS `npm test` (unit + Supertest e2e: auth, users, cart, checkout, coupons, payments, orders, wishlist, catalog/home, health, OpenAPI contract)
- [ ] `.github/workflows/ci.yml` — Flutter `flutter analyze` and `flutter test` in `app/`
- [ ] `.github/workflows/ci.yml` — `docker compose config` for local and staging compose files
- [ ] `apps/api` — OpenAPI byte parity (`openapi.contract.spec.ts`) and 28 counted operationIds (`m3-api.operations.spec.ts`)

## Staging infrastructure

- [ ] `docker compose up --build` — API starts with JWT env (see root `docker-compose.yml` local placeholders)
- [ ] `GET /api/v1/health` returns `{ "status": "ok", "database": "up" }`
- [ ] `node scripts/staging-smoke.mjs` — 28 OpenAPI operationIds, M3 home merchandising, ≥18 seeded SKUs
- [ ] Staging host: `docker compose -f docker-compose.staging.yml` with `DATABASE_URL`, `POSTGRES_PASSWORD`, `JWT_*` from secrets (never in repo)
- [ ] Set `RUN_DB_SEED=false` on production after first seed if you must avoid re-seeding on every deploy

## User journeys (manual spot-check)

| Story | Screen(s) | Spot-check |
| --- | --- | --- |
| US-001 | SCR-01, SCR-02 | Home banners/featured/new arrivals; category listing GBP pence |
| US-002 | SCR-02 | Search SKU/name; filters; sort price/popularity |
| US-003 | SCR-03, SCR-04 | Variants, specs, bundled imagery |
| US-004 | SCR-09, SCR-10 | Register/login/logout; guest cart merge |
| US-005 | SCR-05 | Cart qty/stock cap, subtotals in pence |
| US-006 | SCR-11 | Wishlist auth-only |
| US-007–US-009 | SCR-06, SCR-07 | UK shipping threshold, coupon, mock payment |
| US-010 | SCR-08 | Order confirmation snapshots |
| US-011 | SCR-12 | Signed-in order history/detail |
| US-012 | SCR-09 | Forgot/reset password stub |
| US-013 | SCR-14 | Support + FAQ |
| US-014 | all catalog | 24 SKUs parity; `docs/IMAGE_SOURCES.md` |

## Deploy

- [ ] CI green on `main` / `master` → staging image push + SSH deploy (health curl in workflow)
- [ ] Production: manual workflow_dispatch with `production` target and environment approval

## Contingency

- [ ] Demo without API: `flutter run --dart-define=FORCE_LOCAL_CATALOG=true`
- [ ] Record which mode (API vs local) was used for stakeholder demo
