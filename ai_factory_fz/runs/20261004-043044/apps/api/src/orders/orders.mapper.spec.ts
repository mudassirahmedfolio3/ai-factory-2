import { OrderStatus } from '@prisma/client';
import { parseShippingAddressSnapshot, toOrderDetail, toOrderSummary } from './orders.mapper';

const baseOrder = {
  id: '11111111-1111-4111-8111-111111111111',
  orderNumber: 'LUM-260405-DEMO01',
  userId: '22222222-2222-4222-8222-222222222222',
  guestEmail: null,
  status: OrderStatus.fulfilled,
  currency: 'GBP',
  subtotalCents: 4999,
  discountCents: 0,
  shippingCents: 495,
  vatCents: 0,
  totalCents: 5494,
  deliveryOption: 'STANDARD' as const,
  couponId: null,
  shippingAddressId: null,
  shippingAddressSnapshot: {
    fullName: 'Alex Shopper',
    line1: '10 High Street',
    city: 'London',
    postalCode: 'SW1A 1AA',
    country: 'GB',
  },
  idempotencyKey: null,
  stripePaymentIntentId: null,
  carrierName: 'Royal Mail',
  trackingNumber: 'RM123456789GB',
  paidAt: new Date('2026-10-01T10:00:00.000Z'),
  fulfilledAt: new Date('2026-10-02T10:00:00.000Z'),
  deliveredAt: null,
  cancelledAt: null,
  createdAt: new Date('2026-10-01T09:00:00.000Z'),
  updatedAt: new Date('2026-10-02T10:00:00.000Z'),
  items: [
    {
      id: '33333333-3333-4333-8333-333333333333',
      orderId: '11111111-1111-4111-8111-111111111111',
      variantId: null,
      productName: 'Modern LED Ceiling Light',
      variantLabel: 'White',
      sku: 'CL-1001-WH',
      quantity: 1,
      unitPriceCents: 4999,
      currency: 'GBP',
      lineTotalCents: 4999,
      createdAt: new Date('2026-10-01T09:00:00.000Z'),
      updatedAt: new Date('2026-10-01T09:00:00.000Z'),
    },
  ],
};

describe('orders.mapper', () => {
  it('toOrderSummary exposes customerStatusLabel', () => {
    const summary = toOrderSummary(baseOrder);
    expect(summary.customerStatusLabel).toBe('Shipped');
    expect(summary.status).toBe(OrderStatus.fulfilled);
    expect(summary.createdAt).toBe('2026-10-01T09:00:00.000Z');
  });

  it('toOrderDetail maps line items, address snapshot, and tracking', () => {
    const detail = toOrderDetail(baseOrder);
    expect(detail.items).toHaveLength(1);
    expect(detail.items[0].sku).toBe('CL-1001-WH');
    expect(detail.shippingAddress.fullName).toBe('Alex Shopper');
    expect(detail.tracking.carrierName).toBe('Royal Mail');
    expect(detail.tracking.trackingNumber).toBe('RM123456789GB');
  });

  it('parseShippingAddressSnapshot rejects invalid JSON', () => {
    expect(() => parseShippingAddressSnapshot(null)).toThrow(
      'Invalid shipping address snapshot',
    );
  });
});
