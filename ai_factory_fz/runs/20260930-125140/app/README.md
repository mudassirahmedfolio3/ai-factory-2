# ShopEase app (M1 Speed Demo)

Flutter app for Android (emulator API 28+). There is no backend, no network and no secrets in M1.

## Stack
- go_router for navigation (`lib/core/router`). There is one route per screen: `/`, `/products/:productId`, `/cart`.
- Riverpod for state (`flutter_riverpod`).
- freezed and json_serializable for domain models (`Money`, `ProductSummary`, `ProductDetail`, `ProductVariant`). They match `openapi.yaml`.
- Design tokens (colors, typography, spacing, radii, touch targets) in `lib/core/theme`. Widgets read the theme and never hard-code values.
- All user-visible strings live in `lib/core/l10n/app_strings.dart`.
- Money is integer minor units plus an ISO 4217 code. It is formatted by `MoneyFormatter` (intl, symbol derived from the currency code).

## Run
```
flutter pub get
dart run build_runner build
flutter run            # with an Android emulator (API 28+) running
```

## Checks
```
flutter analyze
flutter test
```

## Folder layout
```
lib/
  app.dart, main.dart
  core/{theme,router,l10n,money,widgets}
  features/catalog/{domain,presentation}
  features/cart/presentation
```

## Network security
Debug builds may reach local staging at `http://10.0.2.2:<port>`. They use `android/app/src/debug/res/xml/network_security_config.xml`, which allows cleartext for 10.0.2.2 only. Release builds keep the default HTTPS-only policy.
