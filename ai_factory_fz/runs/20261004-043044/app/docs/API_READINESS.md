# M2 API catalog readiness (WI-011)

## Stakeholder demo behaviour

- On launch, the app probes `GET /api/v1/health`. When the NestJS API returns `status: ok`, catalog screens (SCR-01–SCR-04) load data through the generated `packages/api_client` dio client via `ApiCatalogDataSource` and `CatalogRepository`.
- When the API is unreachable, health fails, or a catalog call errors, the app **falls back to the M1 embedded catalog** (`assets/data/catalog.json`) so the demo remains usable without backend setup.
- Force local-only mode for CI or manual QA:  
  `flutter run --dart-define=FORCE_LOCAL_CATALOG=true`

## Base URL

| Build | Default base URL |
| --- | --- |
| Debug (Android emulator) | `http://10.0.2.2:3000/api/v1` |
| Override | `--dart-define=API_BASE_URL=https://host/api/v1` |
| Release | `--dart-define=API_BASE_URL_RELEASE=...` (HTTPS only) |

## OpenAPI client generation

The committed client under `packages/api_client` was generated from the contract in `docs/openapi.yaml` (mirrored at `app/openapi.yaml`).

Regenerate after backend changes when **`flutter analyze` and `flutter test` pass**:

1. Start staging API so OpenAPI is served at `http://localhost:3000/api/docs-json` (or export the same document from `docs/openapi.yaml`).
2. From `app/`, run OpenAPI Generator (dart-dio), for example:

```text
openapi-generator-cli generate -i openapi.yaml -g dart-dio -o packages/api_client --additional-properties=pubName=api_client
```

3. Run `dart run build_runner build` inside `packages/api_client` if the generator did not emit `.g.dart` files.
4. Re-run `flutter analyze` and `flutter test` in `app/`.

## Operations wired in the app

| operationId | Used by |
| --- | --- |
| `getHealth` | Session probe before API catalog mode |
| `getHome` | HomeNotifier (SCR-01) |
| `listCategories` | Category browse |
| `getCategoryBySlug` | Listing context |
| `getCatalogFacets` | ProductListNotifier filters (SCR-02) |
| `listProducts` | ProductListNotifier (SCR-02) |
| `getProductById` | ProductDetailNotifier (SCR-03) |
| `listProductReviews` | ReviewsNotifier (SCR-04) |

Money fields use **integer pence** (`amountCents`) with **ISO 4217 `GBP`**, matching M1 mock JSON.

## Verifying API mode

1. Run Docker staging / NestJS API on port 3000 with seeded catalog matching M1 SKUs.
2. Launch the Android emulator build (debug) without `FORCE_LOCAL_CATALOG`.
3. Confirm home and product listing show the same 16 SKU ids as local mocks; compare a detail page price in pence and variant list.

If integration is blocked (codegen drift, analyze failures), ship the demo with local mocks only and track regeneration using the steps above.
