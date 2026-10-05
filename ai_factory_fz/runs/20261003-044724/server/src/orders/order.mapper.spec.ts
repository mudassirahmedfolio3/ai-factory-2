import { describe, expect, it } from 'vitest';
import { mapShopperStatus } from './order.mapper.js';
import { ShopperOrderStatus } from './dto/orders.dto.js';

describe('mapShopperStatus', () => {
  const base = {
    id: 'o1',
    userId: 'u1',
    orderNumber: 'SE-1',
    currency: 'USD',
    subtotalCents: 100,
    discountCents: 0,
    shippingCents: 0,
    taxCents: 0,
    totalCents: 100,
    couponId: null,
    couponCode: null,
    shippingAddressSnapshot: {},
    idempotencyKey: null,
    paidAt: null,
    fulfilledAt: null,
    deliveredAt: null,
    cancelledAt: null,
    paymentExpiresAt: null,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it('maps paid to processing', () => {
    expect(
      mapShopperStatus({ ...base, status: 'paid', carrierName: null, trackingNumber: null }),
    ).toBe(ShopperOrderStatus.PROCESSING);
  });

  it('maps fulfilled with tracking to shipped', () => {
    expect(
      mapShopperStatus({
        ...base,
        status: 'fulfilled',
        carrierName: 'UPS',
        trackingNumber: '1Z999',
      }),
    ).toBe(ShopperOrderStatus.SHIPPED);
  });

  it('maps pending_payment to awaiting_payment', () => {
    expect(
      mapShopperStatus({ ...base, status: 'pending_payment', carrierName: null, trackingNumber: null }),
    ).toBe(ShopperOrderStatus.AWAITING_PAYMENT);
  });

  it('maps fulfilled without tracking to processing', () => {
    expect(
      mapShopperStatus({
        ...base,
        status: 'fulfilled',
        carrierName: null,
        trackingNumber: null,
      }),
    ).toBe(ShopperOrderStatus.PROCESSING);
  });

  it('maps delivered to delivered', () => {
    expect(
      mapShopperStatus({
        ...base,
        status: 'delivered',
        carrierName: 'UPS',
        trackingNumber: '1Z999',
      }),
    ).toBe(ShopperOrderStatus.DELIVERED);
  });

  it('maps cancelled and refunded', () => {
    expect(
      mapShopperStatus({ ...base, status: 'cancelled', carrierName: null, trackingNumber: null }),
    ).toBe(ShopperOrderStatus.CANCELLED);
    expect(
      mapShopperStatus({ ...base, status: 'refunded', carrierName: null, trackingNumber: null }),
    ).toBe(ShopperOrderStatus.REFUNDED);
  });

  /**
   * QA matrix (see shopper-order-status.qa.md) — keep in sync with US-010 / US-011.
   */
  it('documents the full backend → shopperStatus mapping for QA', () => {
    const cases: Array<{
      status:
        | 'pending_payment'
        | 'paid'
        | 'fulfilled'
        | 'delivered'
        | 'cancelled'
        | 'refunded';
      carrierName: string | null;
      trackingNumber: string | null;
      expected: ShopperOrderStatus;
    }> = [
      { status: 'pending_payment', carrierName: null, trackingNumber: null, expected: ShopperOrderStatus.AWAITING_PAYMENT },
      { status: 'paid', carrierName: null, trackingNumber: null, expected: ShopperOrderStatus.PROCESSING },
      { status: 'fulfilled', carrierName: null, trackingNumber: null, expected: ShopperOrderStatus.PROCESSING },
      { status: 'fulfilled', carrierName: 'UPS', trackingNumber: '1Z', expected: ShopperOrderStatus.SHIPPED },
      { status: 'delivered', carrierName: 'UPS', trackingNumber: '1Z', expected: ShopperOrderStatus.DELIVERED },
      { status: 'cancelled', carrierName: null, trackingNumber: null, expected: ShopperOrderStatus.CANCELLED },
      { status: 'refunded', carrierName: null, trackingNumber: null, expected: ShopperOrderStatus.REFUNDED },
    ];

    for (const row of cases) {
      expect(
        mapShopperStatus({
          ...base,
          status: row.status,
          carrierName: row.carrierName,
          trackingNumber: row.trackingNumber,
        }),
      ).toBe(row.expected);
    }
  });
});
