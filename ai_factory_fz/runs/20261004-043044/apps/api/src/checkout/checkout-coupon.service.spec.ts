import { BadRequestException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import {
  COUPON_MINIMUM_NOT_MET_MESSAGE,
  COUPON_NOT_ELIGIBLE_MESSAGE,
  COUPON_NOT_FOUND_MESSAGE,
  COUPON_STACKING_MESSAGE,
} from './checkout.constants';
import { CheckoutCouponService } from './checkout-coupon.service';

describe('CheckoutCouponService', () => {
  let service: CheckoutCouponService;
  let couponFindFirst: jest.Mock;
  let productVariantFindMany: jest.Mock;
  let userFindUnique: jest.Mock;
  let couponRedemptionFindFirst: jest.Mock;

  const cartLine = {
    id: 'line-1',
    variantId: 'var-1',
    productId: 'prod-1',
    productName: 'Light',
    variantLabel: 'White',
    sku: 'SKU-1',
    quantity: 1,
    unitPrice: { amountCents: 6000, currency: 'GBP' },
    lineSubtotalCents: 6000,
    imageUrl: 'img.png',
  };

  beforeEach(() => {
    couponFindFirst = jest.fn();
    productVariantFindMany = jest.fn();
    userFindUnique = jest.fn();
    couponRedemptionFindFirst = jest.fn();

    const prisma = {
      coupon: { findFirst: couponFindFirst },
      productVariant: { findMany: productVariantFindMany },
      user: { findUnique: userFindUnique },
      couponRedemption: { findFirst: couponRedemptionFindFirst },
    } as unknown as PrismaService;

    service = new CheckoutCouponService(prisma);
  });

  it('returns discount preview for a valid coupon', async () => {
    couponFindFirst.mockResolvedValue({
      id: 'cp-1',
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
      categories: [{ categoryId: 'cat-ceiling' }],
      products: [],
    });
    productVariantFindMany.mockResolvedValue([
      {
        id: 'var-1',
        compareAtCents: null,
        product: { id: 'prod-1', categoryId: 'cat-ceiling' },
      },
    ]);

    const result = await service.resolveCouponPreview(
      'ceiling10',
      6000,
      'GBP',
      [cartLine],
      null,
    );

    expect(result.discountCents).toBe(600);
    expect(result.couponCode).toBe('CEILING10');
  });

  it('throws 400 when multiple codes are submitted (stacking)', async () => {
    await expect(
      service.resolveCouponPreview('CEILING10 OUTDOOR15', 6000, 'GBP', [cartLine], null),
    ).rejects.toMatchObject({
      response: {
        statusCode: 400,
        message: COUPON_STACKING_MESSAGE,
      },
    });
    expect(couponFindFirst).not.toHaveBeenCalled();
  });

  it('throws 400 when minimum subtotal is not met', async () => {
    couponFindFirst.mockResolvedValue({
      id: 'cp-1',
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
      categories: [{ categoryId: 'cat-ceiling' }],
      products: [],
    });
    productVariantFindMany.mockResolvedValue([
      {
        id: 'var-1',
        compareAtCents: null,
        product: { id: 'prod-1', categoryId: 'cat-ceiling' },
      },
    ]);

    await expect(
      service.resolveCouponPreview('CEILING10', 4999, 'GBP', [cartLine], null),
    ).rejects.toMatchObject({
      response: {
        statusCode: 400,
        message: COUPON_MINIMUM_NOT_MET_MESSAGE,
      },
    });
  });

  it('throws 400 when scoped coupon does not match cart category', async () => {
    couponFindFirst.mockResolvedValue({
      id: 'cp-1',
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
      categories: [{ categoryId: 'cat-ceiling' }],
      products: [],
    });
    productVariantFindMany.mockResolvedValue([
      {
        id: 'var-1',
        compareAtCents: null,
        product: { id: 'prod-1', categoryId: 'cat-outdoor' },
      },
    ]);

    await expect(
      service.resolveCouponPreview('CEILING10', 6000, 'GBP', [cartLine], null),
    ).rejects.toMatchObject({
      response: {
        statusCode: 400,
        message: COUPON_NOT_ELIGIBLE_MESSAGE,
      },
    });
  });

  it('throws 400 when coupon is unknown', async () => {
    couponFindFirst.mockResolvedValue(null);

    await expect(
      service.resolveCouponPreview('MISSING', 6000, 'GBP', [cartLine], null),
    ).rejects.toMatchObject({
      response: {
        statusCode: 400,
        message: COUPON_NOT_FOUND_MESSAGE,
      },
    });
    await expect(
      service.resolveCouponPreview('MISSING', 6000, 'GBP', [cartLine], null),
    ).rejects.toBeInstanceOf(BadRequestException);
  });
});
