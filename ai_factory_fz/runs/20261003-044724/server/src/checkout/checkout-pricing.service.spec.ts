import { CouponExclusionKind, CouponType } from '@prisma/client';
import { describe, expect, it } from 'vitest';
import { CheckoutPricingService } from './checkout-pricing.service.js';
import { CouponRejectionReason } from './dto/checkout.dto.js';
import type { PricedLineContext } from './checkout-pricing.service.js';

describe('CheckoutPricingService', () => {
  const service = new CheckoutPricingService();

  const storeConfig = {
    id: 1,
    currency: 'USD',
    freeShippingThresholdCents: 7500,
    flatShippingCents: 599,
    taxRateBps: 800,
    lowStockThreshold: 5,
    supportEmail: 'support@shopease-demo.com',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const line: PricedLineContext = {
    variantId: '11111111-1111-1111-1111-111111111111',
    productId: '22222222-2222-2222-2222-222222222222',
    categoryId: '33333333-3333-3333-3333-333333333333',
    quantity: 2,
    unitPriceCents: 2000,
    currency: 'USD',
    productName: 'Soap',
    variantName: 'Large',
    sku: 'SOAP-L',
  };

  it('applies flat shipping below free-shipping threshold and 8% tax after discount', () => {
    const breakdown = service.computeBreakdown([line], storeConfig, null, undefined);

    expect(breakdown.subtotalCents).toBe(4000);
    expect(breakdown.shippingCents).toBe(599);
    expect(breakdown.discountCents).toBe(0);
    expect(breakdown.taxCents).toBe(320);
    expect(breakdown.totalCents).toBe(4919);
  });

  it('waives shipping when subtotal meets threshold', () => {
    const bigLine = { ...line, unitPriceCents: 4000, quantity: 2 };
    const breakdown = service.computeBreakdown([bigLine], storeConfig, null, undefined);

    expect(breakdown.subtotalCents).toBe(8000);
    expect(breakdown.shippingCents).toBe(0);
  });

  it('validates percent coupon and rejects excluded category items', () => {
    const coupon = {
      id: 'c1',
      code: 'GIFTEXCL15',
      type: CouponType.PERCENT,
      percentOff: 15,
      amountOffCents: null,
      currency: 'USD',
      minSubtotalCents: 1000,
      startsAt: null,
      expiresAt: new Date('2099-01-01T00:00:00.000Z'),
      maxRedemptions: null,
      redemptionCount: 0,
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
      exclusions: [
        {
          id: 'e1',
          couponId: 'c1',
          kind: CouponExclusionKind.CATEGORY,
          categoryId: line.categoryId,
          productId: null,
          createdAt: new Date(),
          updatedAt: new Date(),
        },
      ],
    };

    const result = service.validateCoupon([line], 4000, 'USD', coupon, 'GIFTEXCL15');
    expect(result.valid).toBe(false);
    expect(result.rejectionReason).toBe(CouponRejectionReason.EXCLUDED_ITEMS);
  });

  it('applies fixed amount coupon capped at subtotal', () => {
    const coupon = {
      id: 'c2',
      code: 'SAVE500',
      type: CouponType.FIXED_AMOUNT,
      percentOff: null,
      amountOffCents: 500,
      currency: 'USD',
      minSubtotalCents: 0,
      startsAt: null,
      expiresAt: new Date('2099-01-01T00:00:00.000Z'),
      maxRedemptions: null,
      redemptionCount: 0,
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
      exclusions: [],
    };

    const breakdown = service.computeBreakdown([line], storeConfig, coupon, 'SAVE500');
    expect(breakdown.discountCents).toBe(500);
    expect(breakdown.taxCents).toBe(280);
    expect(breakdown.totalCents).toBe(4379);
  });
});
