import {
  COUPON_MINIMUM_NOT_MET_MESSAGE,
  COUPON_NOT_ELIGIBLE_MESSAGE,
  COUPON_STACKING_MESSAGE,
} from './checkout.constants';
import {
  computeCouponDiscountCents,
  CouponValidationError,
  parseCouponCodeInput,
} from './checkout-coupon';
import { CheckoutCouponLine, LoadedCoupon } from './checkout-coupon.types';

const baseCoupon = (overrides: Partial<LoadedCoupon> = {}): LoadedCoupon => ({
  id: 'coupon-id',
  code: 'CEILING10',
  description: '10% off ceiling lighting',
  percentOff: 10,
  amountOffCents: null,
  currency: 'GBP',
  minSubtotalCents: 5000,
  expiresAt: new Date('2027-01-01T00:00:00.000Z'),
  singleUsePerEmail: false,
  excludeSaleItems: true,
  isActive: true,
  categoryIds: ['cat-ceiling'],
  productIds: [],
  ...overrides,
});

const line = (overrides: Partial<CheckoutCouponLine> = {}): CheckoutCouponLine => ({
  productId: 'prod-1',
  variantId: 'var-1',
  lineSubtotalCents: 6000,
  categoryId: 'cat-ceiling',
  isOnSale: false,
  ...overrides,
});

describe('parseCouponCodeInput', () => {
  it('normalizes a single code', () => {
    expect(parseCouponCodeInput('ceiling10')).toEqual(['CEILING10']);
  });

  it('rejects multiple codes as stacking', () => {
    expect(() => parseCouponCodeInput('CEILING10, OUTDOOR15')).toThrow(CouponValidationError);
    try {
      parseCouponCodeInput('CEILING10 OUTDOOR15');
    } catch (error) {
      expect(error).toBeInstanceOf(CouponValidationError);
      expect((error as CouponValidationError).clientMessage).toBe(COUPON_STACKING_MESSAGE);
    }
  });
});

describe('computeCouponDiscountCents', () => {
  it('applies percent discount to eligible category lines', () => {
    const result = computeCouponDiscountCents(
      6000,
      [line({ lineSubtotalCents: 6000 })],
      baseCoupon(),
    );

    expect(result).toEqual({
      couponApplied: true,
      couponCode: 'CEILING10',
      discountCents: 600,
      couponMessage: '10% off ceiling lighting',
    });
  });

  it('rejects when minimum subtotal is not met', () => {
    expect(() =>
      computeCouponDiscountCents(4999, [line({ lineSubtotalCents: 4999 })], baseCoupon()),
    ).toThrow(CouponValidationError);
    try {
      computeCouponDiscountCents(4999, [line({ lineSubtotalCents: 4999 })], baseCoupon());
    } catch (error) {
      expect((error as CouponValidationError).clientMessage).toBe(COUPON_MINIMUM_NOT_MET_MESSAGE);
    }
  });

  it('rejects when cart has no eligible items for scoped coupon', () => {
    expect(() =>
      computeCouponDiscountCents(
        6000,
        [line({ categoryId: 'cat-outdoor', lineSubtotalCents: 6000 })],
        baseCoupon(),
      ),
    ).toThrow(CouponValidationError);
    try {
      computeCouponDiscountCents(
        6000,
        [line({ categoryId: 'cat-outdoor', lineSubtotalCents: 6000 })],
        baseCoupon(),
      );
    } catch (error) {
      expect((error as CouponValidationError).clientMessage).toBe(COUPON_NOT_ELIGIBLE_MESSAGE);
    }
  });

  it('applies fixed amount discount capped by eligible subtotal', () => {
    const result = computeCouponDiscountCents(
      2000,
      [line({ lineSubtotalCents: 2000, categoryId: 'any' })],
      baseCoupon({
        code: 'BULB5',
        percentOff: null,
        amountOffCents: 500,
        minSubtotalCents: 1500,
        categoryIds: [],
        productIds: ['prod-1'],
        excludeSaleItems: false,
      }),
    );

    expect(result.discountCents).toBe(500);
  });

  it('excludes sale lines when excludeSaleItems is true', () => {
    expect(() =>
      computeCouponDiscountCents(
        6000,
        [line({ isOnSale: true, lineSubtotalCents: 6000 })],
        baseCoupon(),
      ),
    ).toThrow(CouponValidationError);
  });
});
