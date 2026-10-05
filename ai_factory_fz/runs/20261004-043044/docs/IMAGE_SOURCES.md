# Catalog imagery provenance (Lumen M3)

Imagery for the Release 2 production-style catalog is sourced from the Stanpro Folio3 staging storefront at [https://stanpro2.folio3.site/search](https://stanpro2.folio3.site/search) and linked product detail pages. Assets are downloaded into the repository for offline demo use and are **not** licensed for production retail without separate agreement with the image owner.

## Use policy

| Environment | Allowed use |
|-------------|-------------|
| Local development | Yes — bundled under `app/assets/catalog/images/` |
| CI / automated tests | Yes — same bundled files (no live fetch in test runs) |
| Staging demo | Yes — API copies under `apps/api/static/catalog/images/` |
| Production retail | No — replace with owned or licensed photography |

## Bundled paths

| Consumer | Path pattern |
|----------|----------------|
| Flutter offline/API fallback | `assets/catalog/images/<product-slug>.jpg` (declared in `app/pubspec.yaml`) |
| NestJS seed JSON | `primaryImageUrl` / variant `imageUrl` / `ProductImage.url` use the same `assets/catalog/images/...` strings returned by catalog mappers |
| API static mirror | `apps/api/static/catalog/images/<filename>` |

Machine-readable download manifest: `apps/api/prisma/data/catalog-image-manifest.json`.  
Regenerate assets (developer machine only): `node apps/api/tools/download-catalog-images.mjs`.

## SKU and source mapping

NetSuite media files are referenced from Stanpro product pages. The staging demo site often reuses the same NetSuite `media.nl` asset across multiple PLP items; each row below records the **canonical Stanpro page** used for provenance even when the binary hash matches.

| Lumen SKU (default variant) | Product slug | Bundled file | Stanpro page URL |
|-----------------------------|--------------|--------------|------------------|
| CL-1001-WH | modern-led-ceiling-light | modern-led-ceiling-light.jpg | https://stanpro2.folio3.site/smart-series-item |
| PD-2201-CH | crystal-pendant-light | crystal-pendant-light.jpg | https://stanpro2.folio3.site/solar-street-light |
| CL-1002-WH | flush-mount-bathroom-light | flush-mount-bathroom-light.jpg | https://stanpro2.folio3.site/recessed-step-light-001-12w-black |
| WL-3001-GR | wall-sconce-duo | wall-sconce-duo.jpg | https://stanpro2.folio3.site/recessed-step-light-003-3w-black |
| WL-3002-AB | picture-light-led | picture-light-led.jpg | https://stanpro2.folio3.site/outdoor-step-light-004-3w-brushed-nickel |
| OS-4001-BK | pir-security-floodlight | pir-security-floodlight.jpg | https://stanpro2.folio3.site/wall-step-light-005-8w-black-name |
| OS-4002-SS | garden-bollard-light | garden-bollard-light.jpg | https://stanpro2.folio3.site/fll-flood-light |
| BT-5001-WW | gu10-led-bulb-5-pack | gu10-led-bulb-5-pack.jpg | https://stanpro2.folio3.site/200000000-223 |
| BT-5002-T8 | t8-led-tube-1200mm | t8-led-tube-1200mm.jpg | https://stanpro2.folio3.site/recessed-step-light-057-15w-matte-black |
| LS-6001-RGB | rgb-led-strip-5m | rgb-led-strip-5m.jpg | https://stanpro2.folio3.site/path-light-017-20w-bronze |
| LS-6002-AL | aluminium-led-profile-2m | aluminium-led-profile-2m.jpg | https://stanpro2.folio3.site/deck-light-014-5w-matte-black |
| LP-7001-GY | bedside-touch-lamp | bedside-touch-lamp.jpg | https://stanpro2.folio3.site/stair-light-007-20w-silver |
| LP-7002-BK | architect-desk-lamp | architect-desk-lamp.jpg | https://stanpro2.folio3.site/recessed-step-light-089-20w-brushed-nickel |
| CT-8001-150 | high-bay-ufo-led | high-bay-ufo-led.jpg | https://stanpro2.folio3.site/tread-light-011-20w-black |
| CT-8002-6060 | panel-light-600x600 | panel-light-600x600.jpg | https://stanpro2.folio3.site/wall-step-light-030-15w-black |
| CT-8003-EX | emergency-exit-sign | emergency-exit-sign.jpg | https://stanpro2.folio3.site/led-step-light-008-20w-silver |
| OS-4003-GY | industrial-bulkhead-light | industrial-bulkhead-light.jpg | https://stanpro2.folio3.site/outdoor-step-light-010-20w-matte-black |
| CL-1003-BK | minimalist-track-spot-3 | minimalist-track-spot-3.jpg | https://stanpro2.folio3.site/surface-step-light-025-20w-silver |
| PD-2202-SM | glass-globe-pendant | glass-globe-pendant.jpg | https://stanpro2.folio3.site/path-light-044-5w-white |
| OS-4004-AN | updown-outdoor-wall-light | updown-outdoor-wall-light.jpg | https://stanpro2.folio3.site/riser-light-031-8w-matte-black |
| BT-5003-WW | mr16-led-bulb-6-pack | mr16-led-bulb-6-pack.jpg | https://stanpro2.folio3.site/deck-light-048-3w-silver |
| CL-1004-WF | smart-wifi-ceiling-fan-light | smart-wifi-ceiling-fan-light.jpg | https://stanpro2.folio3.site/smart-series-item |
| LP-7003-RC | rechargeable-camping-lantern | rechargeable-camping-lantern.jpg | https://stanpro2.folio3.site/path-light-069-3w-matte-black |
| CT-8004-DALI | dali-dimmable-panel-kit | dali-dimmable-panel-kit.jpg | https://stanpro2.folio3.site/stair-light-114-5w-white |

### Home merchandising banners

| Asset | Bundled file | Stanpro reference |
|-------|--------------|-------------------|
| Winter sale banner | winter-sale-banner.jpg | https://stanpro2.folio3.site/search |
| Outdoor security banner | outdoor-security-banner.jpg | https://stanpro2.folio3.site/fll-flood-light |

## Catalog parity

- **Prisma seed**: `apps/api/prisma/data/catalog.json` (24 products, 29 variants, merchandising weights, coupon cross-refs).
- **Flutter offline**: `app/assets/data/catalog.json` (byte-synced copy of the API seed JSON).
- **API responses**: `CatalogMapper` passes through `primaryImageUrl` / image URLs unchanged from the database seed.

Coupon cross-reference slugs in seed JSON align with checkout promo rules seeded alongside the catalog (`CEILING10`, `OUTDOOR15`, `BULB5`).
