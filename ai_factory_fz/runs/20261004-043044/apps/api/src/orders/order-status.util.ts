import { OrderStatus } from '@prisma/client';

const CUSTOMER_STATUS_LABEL: Record<OrderStatus, string> = {
  pending_payment: 'Payment pending',
  paid: 'Processing',
  fulfilled: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  refunded: 'Refunded',
};

export function toCustomerStatusLabel(status: OrderStatus): string {
  return CUSTOMER_STATUS_LABEL[status];
}

export type OrderTrackingFields = {
  carrierName: string | null;
  trackingNumber: string | null;
  estimatedDeliveryCopy: string | undefined;
};

export function buildOrderTracking(order: {
  status: OrderStatus;
  carrierName: string | null;
  trackingNumber: string | null;
  deliveredAt: Date | null;
}): OrderTrackingFields {
  const carrierName = order.carrierName?.trim() || null;
  const trackingNumber = order.trackingNumber?.trim() || null;

  let estimatedDeliveryCopy: string | undefined;
  switch (order.status) {
    case OrderStatus.pending_payment:
      estimatedDeliveryCopy =
        'Complete payment to confirm your order and delivery estimate.';
      break;
    case OrderStatus.paid:
      estimatedDeliveryCopy =
        'Standard UK mainland delivery usually arrives within 3–5 working days.';
      break;
    case OrderStatus.fulfilled:
      estimatedDeliveryCopy = carrierName
        ? 'Your parcel is on its way. Use the tracking reference for the latest delivery estimate.'
        : 'Your order has shipped. Standard UK delivery usually arrives within 1–2 working days.';
      break;
    case OrderStatus.delivered:
      estimatedDeliveryCopy = order.deliveredAt
        ? 'Your order has been delivered.'
        : 'Your order has been delivered.';
      break;
    case OrderStatus.cancelled:
      estimatedDeliveryCopy = 'This order was cancelled.';
      break;
    case OrderStatus.refunded:
      estimatedDeliveryCopy = 'This order was refunded.';
      break;
    default:
      estimatedDeliveryCopy = undefined;
  }

  return {
    carrierName,
    trackingNumber,
    estimatedDeliveryCopy,
  };
}
