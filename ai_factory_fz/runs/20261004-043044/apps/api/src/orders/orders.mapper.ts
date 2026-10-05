import { Order, OrderItem, Prisma } from '@prisma/client';
import { UkAddressInputDto } from '../checkout/dto/uk-address-input.dto';
import { OrderDetailDto } from './dto/order-detail.dto';
import { OrderLineItemDto } from './dto/order-line-item.dto';
import { OrderSummaryDto } from './dto/order-summary.dto';
import { OrderTrackingDto } from './dto/order-tracking.dto';
import { buildOrderTracking, toCustomerStatusLabel } from './order-status.util';

export type OrderWithItems = Order & { items: OrderItem[] };

export function parseShippingAddressSnapshot(
  snapshot: Prisma.JsonValue,
): UkAddressInputDto {
  if (snapshot == null || typeof snapshot !== 'object' || Array.isArray(snapshot)) {
    throw new Error('Invalid shipping address snapshot');
  }
  const record = snapshot as Record<string, unknown>;
  const required = ['fullName', 'line1', 'city', 'postalCode', 'country'] as const;
  for (const key of required) {
    if (typeof record[key] !== 'string' || record[key].length === 0) {
      throw new Error('Invalid shipping address snapshot');
    }
  }
  if (record.country !== 'GB') {
    throw new Error('Invalid shipping address snapshot');
  }
  return {
    fullName: record.fullName as string,
    line1: record.line1 as string,
    line2:
      record.line2 === undefined || record.line2 === null
        ? undefined
        : String(record.line2),
    city: record.city as string,
    region:
      record.region === undefined || record.region === null
        ? undefined
        : String(record.region),
    postalCode: record.postalCode as string,
    country: 'GB',
  };
}

export function toOrderSummary(order: Order): OrderSummaryDto {
  return {
    id: order.id,
    orderNumber: order.orderNumber,
    status: order.status,
    customerStatusLabel: toCustomerStatusLabel(order.status),
    totalCents: order.totalCents,
    currency: order.currency,
    createdAt: order.createdAt.toISOString(),
  };
}

function toOrderLineItem(item: OrderItem): OrderLineItemDto {
  return {
    productName: item.productName,
    variantLabel: item.variantLabel,
    sku: item.sku,
    quantity: item.quantity,
    unitPriceCents: item.unitPriceCents,
    lineTotalCents: item.lineTotalCents,
    currency: item.currency,
  };
}

function toTrackingDto(order: Order): OrderTrackingDto {
  const tracking = buildOrderTracking(order);
  const dto: OrderTrackingDto = {};
  if (tracking.carrierName) {
    dto.carrierName = tracking.carrierName;
  }
  if (tracking.trackingNumber) {
    dto.trackingNumber = tracking.trackingNumber;
  }
  if (tracking.estimatedDeliveryCopy) {
    dto.estimatedDeliveryCopy = tracking.estimatedDeliveryCopy;
  }
  return dto;
}

export function toOrderDetail(order: OrderWithItems): OrderDetailDto {
  return {
    ...toOrderSummary(order),
    items: order.items.map(toOrderLineItem),
    subtotalCents: order.subtotalCents,
    shippingCents: order.shippingCents,
    discountCents: order.discountCents,
    shippingAddress: parseShippingAddressSnapshot(order.shippingAddressSnapshot),
    tracking: toTrackingDto(order),
  };
}
