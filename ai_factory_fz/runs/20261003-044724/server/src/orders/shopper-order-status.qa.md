# Shopper order status labels (QA reference)

Server `backendStatus` values (Prisma `OrderStatus`) are mapped to wire field `shopperStatus` (`ShopperOrderStatus` in OpenAPI) for list and detail responses. Mobile order history and the status stepper must use **`shopperStatus` only**, not raw backend enums.

Implementation: `mapShopperStatus()` in `order.mapper.ts`.

| Backend status (`backendStatus`) | Wire `shopperStatus` | QA notes |
| --- | --- | --- |
| `pending_payment` | `awaiting_payment` | Checkout created; mock payment not completed. |
| `paid` | `processing` | Demo “paid / being prepared”; no carrier tracking yet. |
| `fulfilled` (no carrier + tracking) | `processing` | Paid/fulfilled without shipment data stays on processing step. |
| `fulfilled` (with `carrierName` and `trackingNumber`) | `shipped` | Seeded demo order `SE-20261004-SHIP01` uses this path. |
| `delivered` | `delivered` | Seeded demo order includes tracking when present in seed. |
| `cancelled` | `cancelled` | Cancelled or abandoned payable order; stock reservation released per server rules. |
| `refunded` | `refunded` | Post-payment refund demo state. |

## Status stepper (US-011)

Display progression for shoppers:

1. **processing** — highlight when `shopperStatus` is `processing` (covers backend `paid`, and `fulfilled` without tracking).
2. **shipped** — highlight when `shopperStatus` is `shipped`.
3. **delivered** — highlight when `shopperStatus` is `delivered`.

Orders in `awaiting_payment` show payment pending (not on the fulfillment stepper). Show **carrier name and tracking number** only when the API returns them (typically `shipped` / `delivered` with seeded fulfillment data).

## Automated checks

Unit tests in `order.mapper.spec.ts` lock the mapping above. E2E with seeded DB (`demo@shopease.test` / `DemoPass123!`) validates `listOrders` / `getOrderById` return expected `shopperStatus` for shipped and delivered demo orders.
