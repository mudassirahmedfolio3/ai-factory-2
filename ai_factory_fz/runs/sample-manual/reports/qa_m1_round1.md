<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. -->
# QA report: Milestone M1 (Shop and cart), round 1

passed: false

Built items checked: WI-001 products API, WI-002 cart API, WI-003 auth and health, WI-004 product list and detail screens, WI-005 cart screen.

## Acceptance criteria, mapped to code and tests

### US-001 Browse products
| Criterion | Code | Test | Result |
|---|---|---|---|
| Each product shows name, price in USD and picture | `app/lib/components/product_card.dart`, `product_list_screen.dart` | `app/test/product_list_screen_test.dart` "shows name and price for each product" | verified |
| Loading state while the API has not answered | `state_view.dart` (loading) | `product_list_screen_test.dart` "shows a loading state..." | verified |
| Empty-state message when there are no products | `product_list_screen.dart` | `product_list_screen_test.dart` "shows the empty state..." | verified |

### US-002 View product details
| Criterion | Code | Test | Result |
|---|---|---|---|
| Detail screen shows name, picture, price, description | `product_detail_screen.dart` | `integration_test/shop_journey_test.dart` first journey | verified |
| Missing product shows an error with a way back | `product_detail_screen.dart` error branch; API returns 404 from `products.controller.ts` | none found | **not covered by a test** (see BUG-2) |

### US-003 Add to cart
| Criterion | Code | Test | Result |
|---|---|---|---|
| Adding a product puts it in the cart with quantity 1 | `cart.service.ts addItem` | `integration_test/shop_journey_test.dart` first journey ("x 1 =") | verified |
| Adding again increases the quantity by 1 | `cart.service.ts addItem` (increment) | `integration_test/shop_journey_test.dart` second journey ("x 2 =") | verified |

### US-004 View cart and total
| Criterion | Code | Test | Result |
|---|---|---|---|
| Each line shows name, unit price, quantity, line total; cart shows total in USD | `cart_screen.dart` | `app/test/cart_screen_test.dart` "each line shows..." | verified |
| Changing a quantity recalculates line and cart totals | `quantity_stepper.dart`, `cart.service.ts setQuantity` | `cart_screen_test.dart` "changing a quantity..." | verified |
| Empty cart shows an empty-state message | `cart_screen.dart` | `cart_screen_test.dart` "empty cart shows the empty state" | verified |

## Non-functional requirements
- Performance (list within 2 s): not measured in this round; no load test exists. Recorded as a gap, not a bug.
- Security: no secrets in the app or in `server/src`; JWT guard is global, only `POST /auth/anonymous` and `GET /health` are public; inputs validated with class-validator and `ValidationPipe`. HTTPS is a production setting, not testable on staging.
- Privacy: only the device id is stored (`Cart.deviceId`); no personal data.
- Accessibility: touch targets are 48dp (`Tokens.minTouchTarget`); contrast comes from the design tokens (WCAG AA values in `theme.dart`). Not verified with a screen reader.
- Platforms: only the Android emulator was available; iOS not checked.

## OpenAPI check (docs/openapi.yaml vs `server/src`)
`getHealth`, `createAnonymousSession`, `listProducts`, `getProduct`, `getCart`, `addCartItem` and `updateCartItemQuantity` are all implemented with the contract's paths, methods and status codes (200, 400, 401, 404). No endpoint exists beyond the contract.

## Bugs

### BUG-1 (major) - work item WI-005 "Cart screen"
Criterion: US-004 "Given an empty cart, When I open it, Then an empty-state message is shown".
- Steps: 1. Fresh install. 2. Tap Cart immediately after launch.
- Expected: the empty-state message, or the loading indicator while the cart loads.
- Actual: a blank screen for about one second before the message appears.
- Severity reason: an acceptance criterion is not fully met (major). It does not break the milestone goal.

### BUG-2 (minor) - work item WI-004 "Product detail"
- Steps: 1. Open `/products/does-not-exist`. 2. Observe.
- Expected: "This product is no longer available." with a way back.
- Actual: message and button are correct, but the "Try again" label is shown instead of "Back to shop" as in the design system.
- Severity reason: cosmetic label difference (minor).

No blocker bugs. The `passed` flag is false because BUG-1 is a major bug.
