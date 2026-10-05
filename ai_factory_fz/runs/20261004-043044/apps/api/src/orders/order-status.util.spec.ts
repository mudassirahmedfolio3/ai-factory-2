import { OrderStatus } from '@prisma/client';
import { buildOrderTracking, toCustomerStatusLabel } from './order-status.util';

describe('toCustomerStatusLabel', () => {
  it('maps backend statuses to shopper-facing labels', () => {
    expect(toCustomerStatusLabel(OrderStatus.pending_payment)).toBe('Payment pending');
    expect(toCustomerStatusLabel(OrderStatus.paid)).toBe('Processing');
    expect(toCustomerStatusLabel(OrderStatus.fulfilled)).toBe('Shipped');
    expect(toCustomerStatusLabel(OrderStatus.delivered)).toBe('Delivered');
    expect(toCustomerStatusLabel(OrderStatus.cancelled)).toBe('Cancelled');
    expect(toCustomerStatusLabel(OrderStatus.refunded)).toBe('Refunded');
  });
});

describe('buildOrderTracking', () => {
  it('includes carrier and tracking when seeded on the order', () => {
    const tracking = buildOrderTracking({
      status: OrderStatus.fulfilled,
      carrierName: 'Royal Mail',
      trackingNumber: 'RM123456789GB',
      deliveredAt: null,
    });
    expect(tracking.carrierName).toBe('Royal Mail');
    expect(tracking.trackingNumber).toBe('RM123456789GB');
    expect(tracking.estimatedDeliveryCopy).toContain('on its way');
  });

  it('returns delivered copy for delivered orders', () => {
    const tracking = buildOrderTracking({
      status: OrderStatus.delivered,
      carrierName: 'DPD',
      trackingNumber: 'DPD998877',
      deliveredAt: new Date('2026-10-01T12:00:00.000Z'),
    });
    expect(tracking.estimatedDeliveryCopy).toBe('Your order has been delivered.');
  });
});
