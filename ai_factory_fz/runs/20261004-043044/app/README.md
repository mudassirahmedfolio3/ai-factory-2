# shopease_app

Lighting Retail UK Flutter app (M1 local catalog, M2 catalog API, M3 shopper depth).

## Catalog data sources

- **M1 default:** `LocalCatalogDataSource` (`assets/data/catalog.json`).
- **M2 API:** Generated `packages/api_client` (dart-dio) via `ApiCatalogDataSource`, selected when `GET /health` succeeds.
- **Demo fallback:** Automatic switch back to local mocks if the API is down.

See [docs/API_READINESS.md](docs/API_READINESS.md) for stakeholder demo notes, OpenAPI regeneration, and dart-define flags.

## Commands

Run from this directory:

```text
flutter pub get
flutter analyze
flutter test
```
