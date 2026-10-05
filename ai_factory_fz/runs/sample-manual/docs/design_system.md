<!-- SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline. -->
# Design System: ShopEase Mini

## Colors
| Token | Light | Dark |
|---|---|---|
| primary | #1F6FEB | #58A6FF |
| background | #FFFFFF | #0D1117 |
| surface | #F6F8FA | #161B22 |
| onSurface | #1F2328 | #E6EDF3 |
| error | #CF222E | #FF7B72 |

Text contrast is at least WCAG AA in both themes.

## Typography
Headline 22/28 semi-bold, title 18/24 medium, body 16/24 regular, caption 12/16.

## Spacing and touch targets
Spacing scale 4, 8, 16, 24. Minimum touch target 48dp.

## Components
- **ProductCard**: picture, name, price in USD. Tap opens the detail screen.
- **QuantityStepper**: minus / quantity / plus buttons, 48dp each.
- **StateView**: shared loading spinner, empty message and error message with a "Try again" button.
- **PrimaryButton**: filled button with the primary color.

## Navigation
go_router with a bottom bar: Shop (/) and Cart (/cart). Product detail is pushed on top at /products/:id.

## Screens

### SCR-01 Product list (path: /) - serves US-001
Components: ProductCard, StateView.
- Loading: centered spinner with "Loading products".
- Empty: "No products yet. Check back soon."
- Error: "We couldn't load products." with a "Try again" button.

### SCR-02 Product detail (path: /products/:id) - serves US-002, US-003
Components: PrimaryButton ("Add to cart"), StateView.
- Loading: spinner while the product loads.
- Empty: not applicable; a missing product shows the error state.
- Error: "This product is no longer available." with a "Back to shop" button.

### SCR-03 Cart (path: /cart) - serves US-003, US-004
Components: QuantityStepper, StateView, total row in USD.
- Loading: spinner while the cart loads.
- Empty: "Your cart is empty. Browse products to add some."
- Error: "We couldn't load your cart." with a "Try again" button.
