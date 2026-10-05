# Lighting Retail UK — monorepo

Dual-stack Release 2 (M3): Flutter shopper app (`app/`, shopease_app) and NestJS API (`apps/api`) with PostgreSQL 16.

## Quick start (local)

```bash
docker compose up --build
```

API: `http://localhost:3000/api/v1/health`  
OpenAPI JSON: `http://localhost:3000/api/docs-json`  
Android emulator base URL (debug): `http://10.0.2.2:3000/api/v1`

Copy `apps/api/.env.example` to `apps/api/.env` when running the API outside Docker.

## Staging compose

Provide secrets via environment (never commit them):

```bash
export POSTGRES_PASSWORD=...
export DATABASE_URL=postgresql://lighting:${POSTGRES_PASSWORD}@postgres:5432/lighting_retail?schema=public
docker compose -f docker-compose.staging.yml up --build
```

## Mobile release networking

Android debug cleartext to the host API is configured under `app/android/app/src/debug`. Release builds must use HTTPS only (see `app/docs/API_READINESS.md`).

## M3 verification (WI-026)

- **Runbook & sign-off:** [app/docs/DEMO_RUNBOOK.md](app/docs/DEMO_RUNBOOK.md), [app/docs/M3_RELEASE2_SIGNOFF.md](app/docs/M3_RELEASE2_SIGNOFF.md)
- **Backend smoke (28 ops + getHealth):** `docker compose up --build` then `node scripts/staging-smoke.mjs` (or `npm run smoke:staging` from `apps/api`)
- **Guest mobile journey:** `scripts/run-guest-catalog-integration.ps1` (forces local catalog fallback for reliable CI/emulator runs)
- **QA report:** [reports/qa_M3_round1.md](reports/qa_M3_round1.md)

## CI

GitHub Actions runs NestJS Jest (`apps/api`) and Flutter analyze/test (`app/`, M1 `shopease_app`) on push and pull requests.

## Deploy (staging and production)

Images are built from `apps/api/Dockerfile` and pushed to GitHub Container Registry by `.github/workflows/deploy.yml`.

| Trigger | Target | GitHub environment |
| --- | --- | --- |
| CI succeeds on `main` / `master` | Staging (`:staging` tag) | `staging` |
| Manual **Deploy** workflow, input `production` | Production (`:production` tag) | `production` (requires reviewer approval) |

Configure repository **Environments** (`staging`, `production`) and secrets (never commit values):

- `STAGING_HOST`, `STAGING_SSH_USER`, `STAGING_SSH_KEY`, `STAGING_DEPLOY_PATH`
- `STAGING_POSTGRES_PASSWORD`, `STAGING_DATABASE_URL`
- `STAGING_JWT_ACCESS_SECRET`, `STAGING_JWT_REFRESH_SECRET` (min 16 characters each)
- `PRODUCTION_HOST`, `PRODUCTION_SSH_USER`, `PRODUCTION_SSH_KEY`, `PRODUCTION_DEPLOY_PATH`
- `PRODUCTION_POSTGRES_PASSWORD`, `PRODUCTION_DATABASE_URL`
- `PRODUCTION_JWT_ACCESS_SECRET`, `PRODUCTION_JWT_REFRESH_SECRET`

On each host, clone this repo and set `API_IMAGE=ghcr.io/<owner>/<repo>/api:staging` (or `:production`) before `docker compose -f docker-compose.staging.yml up -d`. The workflow runs the same compose file over SSH after `docker compose pull api`.

Local staging without a registry: omit `API_IMAGE` to build from source, or set `API_IMAGE=lighting-retail-api:local`.
