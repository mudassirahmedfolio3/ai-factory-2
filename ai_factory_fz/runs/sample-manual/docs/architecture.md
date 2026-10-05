<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. -->
# Architecture: ShopEase Mini

## Components
- **Mobile app (Flutter)**: Android and iOS client. Responsible for UI, cart state and calling the API.
- **API server (NestJS + TypeScript)**: REST API, validation, business rules.
- **PostgreSQL**: stores products and carts, accessed through Prisma.

## Backend modules
- **ProductsModule**: entity Product; endpoints GET /products, GET /products/{id}.
- **CartModule**: entities Cart, CartItem; endpoints GET /cart, POST /cart/items, PATCH /cart/items/{productId}.

## Mobile app features
- **Product list screen** (US-001): loading, empty and error states. State: Riverpod AsyncNotifier.
- **Product detail screen** (US-002): shows description, "Add to cart" (US-003).
- **Cart screen** (US-004): lines, quantities, total in USD. State: Riverpod Notifier, synced with API.

## Security design
- HTTPS only in production; HSTS enabled.
- Bearer token auth: an anonymous device id is exchanged for a signed JWT; no personal data stored.
- Input validation on every endpoint (class-validator); rate limiting at 100 req/min per device.
- No secrets in the app; server secrets come from environment variables.

## ADRs
### ADR-001: NestJS for the API
Context: team knows TypeScript; need modules and validation. Decision: NestJS. Consequences: opinionated structure, faster onboarding, heavier than Express.
### ADR-002: PostgreSQL with Prisma
Context: relational data (carts to products). Decision: PostgreSQL + Prisma. Consequences: type-safe queries, migrations to manage.
### ADR-003: Anonymous device identity
Context: no sign-in, but carts must persist. Decision: device id exchanged for a JWT. Consequences: cart lost if app data is cleared; no PII stored.
