# Lighting Retail UK — monorepo

Dual-stack MVP: Flutter mobile (`apps/mobile`) and NestJS API (`apps/api`) with PostgreSQL 16.

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

See [apps/mobile/NETWORK_SECURITY.md](apps/mobile/NETWORK_SECURITY.md) for HTTPS-only release policy and debug cleartext rules.

## CI

GitHub Actions runs NestJS Jest (`apps/api`) and Flutter analyze/test (`apps/mobile`) on push and pull requests.
