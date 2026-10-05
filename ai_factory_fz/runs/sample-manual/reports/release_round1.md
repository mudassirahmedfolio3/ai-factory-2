<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. -->
# Release verification: round 1

passed: false

Environment: staging from `infra/docker-compose.staging.yml` (API on :3000, PostgreSQL 16). Contract: `docs/openapi.yaml`.
Evidence below is the actual request and response seen during this round.

## 1. Configuration and environment variables
`docker compose logs api` showed the app started with `PORT=3000`, `DATABASE_URL` set and `JWT_SECRET` set (all from `infra/staging.env`). `CORS_ORIGINS` was empty. Result: OK.

## 2. API prefix
All paths answered without a prefix, as in the contract (`servers: https://api.shopease.example`, no base path). Result: OK.

## 3. Database migrations
Log line on start: `prisma migrate deploy ... 1 migration applied: init`. Tables Product, Cart, CartItem exist (`\dt` in psql). Result: OK.

## 4. CORS and security headers
`curl -i http://localhost:3000/health` returned `x-content-type-options: nosniff`, `strict-transport-security: max-age=15552000` and no `x-powered-by`. A preflight from the app origin returned 204 with the allowed origin only when `CORS_ORIGINS` listed it. Result: OK.

## 5. Authentication
- `POST /auth/anonymous {"deviceId":"release-check-1"}` -> `200 {"token":"<jwt>"}` (matches `Session`).
- `POST /auth/anonymous {}` -> `400 {"code":"VALIDATION_ERROR","message":"deviceId must be longer than or equal to 8 characters; deviceId must be a string"}` (matches the contract's 400 and the `Error` schema).
- `GET /products` without a token -> `401 {"code":"UNAUTHORIZED",...}`. With the token -> `200`. Result: OK.

## 6. Error format
`GET /products/does-not-exist` with token -> `404 {"code":"NOT_FOUND","message":"Product not found"}`. Matches the `Error` schema. Result: OK.

## 7. Endpoint-by-endpoint contract match
| operationId | Request | Observed | Matches contract |
|---|---|---|---|
| getHealth | `GET /health` | 200 `{"status":"ok"}` | yes |
| createAnonymousSession | see section 5 | 200 / 400 | yes |
| listProducts | `GET /products?page=1&pageSize=2` | 200, `items` length 2, `page`, `pageSize`, `total` present | **no**: item field `price` (decimal) instead of `priceCents` (integer) |
| getProduct | `GET /products/{id}` | 200 | **no**: same `price` field problem |
| getCart | `GET /cart` | 200 `{"items":[],"totalCents":0}` | yes |
| addCartItem | `POST /cart/items {"productId":"<id>"}` twice | 200, `quantity` 1 then 2 | yes |
| updateCartItemQuantity | `PATCH /cart/items/<id> {"quantity":0}` | 200, item removed; unknown id -> 404 | yes |

## Bugs

### BUG-1 (major) - work item WI-001 (products API)
`GET /products` and `GET /products/{id}` return `price` (decimal, for example `59.0`) instead of `priceCents` (integer, for example `5900`) required by the `Product` schema.
- Steps: `GET /products?page=1&pageSize=1` with a valid token.
- Expected: `items[0].priceCents == 5900`.
- Actual: `items[0].price == 59.0`, no `priceCents`.
- Severity: major, a contract mismatch. The app computes totals from `priceCents`, but the cart endpoints are correct, so the built journeys still work.

No blocker bugs: every built journey (sign in, browse, add to cart, change quantity) could be served. The `passed` flag is false because of the major bug above.
