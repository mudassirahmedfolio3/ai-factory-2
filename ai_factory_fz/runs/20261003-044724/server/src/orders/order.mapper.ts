import type { Order, OrderItem, OrderStatus } from '@prisma/client';
import type { ShippingAddressDto } from '../checkout/dto/checkout.dto.js';
import {
  BackendOrderStatus,
  type OrderDetailDto,
  type OrderLineItemDto,
  type OrderSummaryDto,
  ShopperOrderStatus,
} from './dto/orders.dto.js';

type OrderWithItems = Order & { items: OrderItem[] };

export function mapShopperStatus(order: Order): ShopperOrderStatus {
  switch (order.status) {
    case 'pending_payment':
      return ShopperOrderStatus.AWAITING_PAYMENT;
    case 'paid':
      return ShopperOrderStatus.PROCESSING;
    case 'fulfilled':
      if (order.carrierName && order.trackingNumber) {
        return ShopperOrderStatus.SHIPPED;
      }
      return ShopperOrderStatus.PROCESSING;
    case 'delivered':
      return ShopperOrderStatus.DELIVERED;
    case 'cancelled':
      return ShopperOrderStatus.CANCELLED;
    case 'refunded':
      return ShopperOrderStatus.REFUNDED;
    default:
      return ShopperOrderStatus.PROCESSING;
  }
}

export function mapBackendStatus(status: OrderStatus): BackendOrderStatus {
  return status as BackendOrderStatus;
}

export function toOrderSummary(order: Order): OrderSummaryDto {
  return {
    id: order.id,
    orderNumber: order.orderNumber,
    createdAt: order.createdAt.toISOString(),
    total: { amountCents: order.totalCents, currency: order.currency },
    shopperStatus: mapShopperStatus(order),
  };
}

export function toOrderDetail(order: OrderWithItems): OrderDetailDto {
  const shippingAddress =
    order.shippingAddressSnapshot as unknown as ShippingAddressDto;
  const money = (amountCents: number) => ({
    amountCents,
    currency: order.currency,
  });

  const lines: OrderLineItemDto[] = order.items.map((item) => ({
    productName: item.productName,
    variantName: item.variantName,
    sku: item.sku,
    quantity: item.quantity,
    unitPrice: { amountCents: item.unitPriceCents, currency: item.currency },
    lineTotal: { amountCents: item.lineTotalCents, currency: item.currency },
  }));

  return {
    id: order.id,
    orderNumber: order.orderNumber,
    createdAt: order.createdAt.toISOString(),
    shopperStatus: mapShopperStatus(order),
    backendStatus: mapBackendStatus(order.status),
    lines,
    subtotal: money(order.subtotalCents),
    discount: money(order.discountCents),
    shipping: money(order.shippingCents),
    tax: money(order.taxCents),
    total: money(order.totalCents),
    couponCode: order.couponCode ?? undefined,
    shippingAddress,
    carrierName: order.carrierName ?? undefined,
    trackingNumber: order.trackingNumber ?? undefined,
  };
}
