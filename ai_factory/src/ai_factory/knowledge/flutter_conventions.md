# Flutter Conventions for E-commerce Apps

## Recommended project structure

```
lib/
├── main.dart
├── app.dart
├── config/           # env, theme, routes
├── core/             # constants, errors, utils
├── data/             # models, repositories, api clients
├── domain/           # entities, use cases (optional clean arch)
├── features/
│   ├── catalog/
│   ├── cart/
│   ├── checkout/
│   ├── orders/
│   └── auth/
└── shared/           # widgets, extensions
```

## State management

- Prefer **Riverpod** or **Bloc** for predictable state in cart/checkout flows.
- Keep cart state global; scope product lists per feature.

## Navigation

- Use **go_router** for deep links (product pages, order details).
- Guard auth-required routes (checkout, orders).

## Testing

- Unit tests for repositories and cart logic.
- Widget tests for critical flows (add to cart, checkout steps).
- Integration tests for happy-path purchase flow.

## Dependencies (typical)

- `http` or `dio` for API
- `flutter_riverpod` or `flutter_bloc`
- `go_router`
- `freezed` + `json_serializable` for models
- `flutter_dotenv` for env config (no secrets in source)

## Code quality

- Null-safe Dart throughout.
- Separate UI from business logic.
- Use design tokens (spacing, colors) in theme, not hardcoded values.
