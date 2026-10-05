# M2 stakeholder demo runbook (WI-012)

## Audience and goal

Demonstrate guest shopping across **SCR-01 Home**, **SCR-02 Product listing**, **SCR-03 Product detail**, **SCR-04 Reviews**, **SCR-05 Cart**, and **SCR-06 App shell** with either:

1. **API mode** — NestJS catalog + health on port 3000, or  
2. **Fallback mode** — embedded M1 catalog (`assets/data/catalog.json`) when the API is down.

## Device requirements

- **Android API 26+** (emulator or physical device).
- Debug build with cleartext allowed to `10.0.2.2` (emulator → host API). See `app/android` network security config.

## Seed catalog (M1 / M2 parity)

| Metric | Value |
| --- | --- |
| Products | 16 |
| Variants | 20 |
| Brands | 5 |
| Top-level categories | 7 (+ subcategories in seed) |
| Featured on home | 4 |

**Taxonomy (top-level):** Ceiling Lights, Wall Lights, Outdoor & Security, Bulbs & Tubes, LED Strips & Profiles, Lamps & Portable, Commercial & Trade.

**Spot-check SKUs (demo script):**

| SKU | Product | Default price (pence) |
| --- | --- | --- |
| CL-1001-WH | Modern LED Ceiling Light | 4999 (£49.99) |
| CL-1001-BK | Modern LED Ceiling Light (Matte Black variant) | 5299 (out of stock in seed) |

Full product ids match `app/assets/data/catalog.json` and `apps/api/prisma/data/catalog.json` (example detail id: `p1111111-1111-4111-8111-111111111101`).

## API base URLs

| Scenario | Base URL |
| --- | --- |
| Android emulator → Docker on host | `http://10.0.2.2:3000/api/v1` |
| Host browser / curl | `http://localhost:3000/api/v1` |
| Override | `flutter run --dart-define=API_BASE_URL=https://your-host/api/v1` |

**OpenAPI (not counted in 12 ops):** `GET http://localhost:3000/api/docs-json`

## Start backend (API mode)

```bash
docker compose up --build
```

Wait for health:

```bash
curl -s http://localhost:3000/api/v1/health
```

Run automated smoke (M3: 28 operationIds + getHealth + OpenAPI + seed count):

```bash
node scripts/staging-smoke.mjs
```

Staging profile (secrets via env, not in repo):

```bash
export POSTGRES_PASSWORD=...
export DATABASE_URL=postgresql://lighting:${POSTGRES_PASSWORD}@postgres:5432/lighting_retail?schema=public
export JWT_ACCESS_SECRET=...   # min 16 chars, from secret store
export JWT_REFRESH_SECRET=...
docker compose -f docker-compose.staging.yml up --build
API_BASE_URL=http://localhost:3000 node scripts/staging-smoke.mjs
```

## Start mobile app

**API mode (default in debug when health succeeds):**

```bash
cd app
flutter pub get
flutter run
```

**Force M1 local mocks (API intentionally off):**

```bash
flutter run --dart-define=FORCE_LOCAL_CATALOG=true
```

## Fallback behaviour (must work on demo day)

1. If `GET /api/v1/health` fails or times out (~2s), the session uses **local catalog** for all reads.
2. If health succeeded but a catalog call fails, the repository **falls back to local** for that session (except true 404s from the API).
3. Stakeholders can always demo with `FORCE_LOCAL_CATALOG=true` if the backend is unavailable.

See `app/docs/API_READINESS.md` for client wiring details.

## Guest path automation

**Integration test (local catalog, no API):**

```powershell
.\scripts\run-guest-catalog-integration.ps1
```

```bash
./scripts/run-guest-catalog-integration.sh
```

Manual checklist:

- [ ] Home shows category grid and featured carousel (not Flutter counter demo).
- [ ] Products tab lists 16 SKUs with GBP prices and out-of-stock badges where seeded.
- [ ] Search `Modern LED` or SKU `CL-1001` filters listing.
- [ ] Product detail shows specs (e.g. 24W, IP44), variants, reviews preview.
- [ ] Reviews screen lists seeded review copy.
- [ ] Add to cart → cart tab shows line with correct unit price snapshot.

## M3 catalog (Release 2)

| Metric | Value |
| --- | --- |
| Products | 24 |
| Variants | 29 |
| Coupons (seed) | 3 |
| Counted API operations | 28 (+ getHealth) |

Sign-off checklist: [M3_RELEASE2_SIGNOFF.md](M3_RELEASE2_SIGNOFF.md).

## Release sign-off checklist (M2)

### Backend

- [ ] `npm test` in `apps/api` (Supertest e2e for all operationIds + contract tests).
- [ ] `node scripts/staging-smoke.mjs` against running compose stack.
- [ ] `GET /api/docs-json` matches `docs/openapi.yaml`.

### Mobile

- [ ] `flutter analyze` and `flutter test` in `app/`.
- [ ] Guest integration script passes with `FORCE_LOCAL_CATALOG=true`.
- [ ] Optional: emulator run without `FORCE_LOCAL_CATALOG` while API is up — listing matches 16-product seed.

### Demo contingency

- [ ] Document which mode was used (API vs local) on the demo recording/slide.
- [ ] If API mode fails mid-demo, relaunch with `FORCE_LOCAL_CATALOG=true`.
