import { BadRequestException, ConflictException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { OrderStatus, Prisma } from '@prisma/client';
import { CartService } from '../cart/cart.service';
import { PrismaService } from '../prisma/prisma.service';
import { CheckoutCouponService } from './checkout-coupon.service';
import { CheckoutService } from './checkout.service';
import { CheckoutPreviewRequestDto } from './dto/checkout-preview-request.dto';
import { CreateOrderRequestDto } from './dto/create-order-request.dto';

describe('CheckoutService', () => {
  let service: CheckoutService;
  let getCartForCheckout: jest.Mock;
  let resolveCouponPreview: jest.Mock;

  const previewRequest = (): CheckoutPreviewRequestDto => ({
    shippingAddress: {
      fullName: 'Alex Smith',
      line1: '10 High Street',
      city: 'London',
      postalCode: 'SW1A 1AA',
      country: 'GB',
    },
  });

  let checkoutIdempotencyFindUnique: jest.Mock;
  let transaction: jest.Mock;
  let couponFindFirst: jest.Mock;

  const createOrderRequest = (): CreateOrderRequestDto => ({
    shippingAddress: previewRequest().shippingAddress,
    contactEmail: 'shopper@example.com',
  });

  beforeEach(() => {
    getCartForCheckout = jest.fn();
    resolveCouponPreview = jest.fn();
    checkoutIdempotencyFindUnique = jest.fn().mockResolvedValue(null);
    couponFindFirst = jest.fn();
    transaction = jest.fn();

    const cartService = { getCartForCheckout } as unknown as CartService;
    const checkoutCouponService = {
      resolveCouponPreview,
    } as unknown as CheckoutCouponService;
    const prisma = {
      checkoutIdempotency: { findUnique: checkoutIdempotencyFindUnique },
      coupon: { findFirst: couponFindFirst },
      $transaction: transaction,
    } as unknown as PrismaService;
    const configService = {
      get: jest.fn((key: string) => {
        if (key === 'UK_SHIPPING_FLAT_RATE_CENTS') {
          return 495;
        }
        if (key === 'UK_FREE_DELIVERY_THRESHOLD_CENTS') {
          return 7500;
        }
        return undefined;
      }),
    } as unknown as ConfigService;

    service = new CheckoutService(cartService, checkoutCouponService, prisma, configService);
  });

  it('returns preview totals with shipping below threshold', async () => {
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 4999,
      currency: 'GBP',
      items: [],
      id: 'cart',
      itemCount: 1,
    });

    const result = await service.previewCheckout(null, 'guest-cart-id', previewRequest());

    expect(result).toEqual({
      subtotalCents: 4999,
      shippingCents: 495,
      discountCents: 0,
      totalCents: 5494,
      currency: 'GBP',
      shippingLabel: 'Standard UK domestic delivery only',
      freeDeliveryThresholdCents: 7500,
      couponApplied: false,
    });
  });

  it('returns free shipping at threshold', async () => {
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 7500,
      currency: 'GBP',
      items: [],
      id: 'cart',
      itemCount: 1,
    });

    const result = await service.previewCheckout(null, 'guest-cart-id', previewRequest());

    expect(result.shippingCents).toBe(0);
    expect(result.totalCents).toBe(7500);
    expect(result.shippingLabel).toBe('Free standard UK domestic delivery');
  });

  it('applies coupon discount to preview totals', async () => {
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 6000,
      currency: 'GBP',
      items: [{ lineSubtotalCents: 6000 }],
      id: 'cart',
      itemCount: 1,
    });
    resolveCouponPreview.mockResolvedValue({
      couponApplied: true,
      couponCode: 'CEILING10',
      discountCents: 600,
      couponMessage: '10% off ceiling lighting',
    });

    const result = await service.previewCheckout(null, 'guest-cart-id', {
      ...previewRequest(),
      couponCode: 'CEILING10',
    });

    expect(resolveCouponPreview).toHaveBeenCalled();
    expect(result.discountCents).toBe(600);
    expect(result.totalCents).toBe(5895);
    expect(result.couponApplied).toBe(true);
    expect(result.couponCode).toBe('CEILING10');
  });

  it('rejects non-mainland addresses', async () => {
    await expect(
      service.previewCheckout(null, 'guest-cart-id', {
        shippingAddress: {
          ...previewRequest().shippingAddress,
          postalCode: 'BT1 1AA',
        },
      }),
    ).rejects.toBeInstanceOf(BadRequestException);
    expect(getCartForCheckout).not.toHaveBeenCalled();
  });

  it('requires Idempotency-Key for createOrder', async () => {
    await expect(
      service.createOrder(null, 'guest-cart-id', undefined, createOrderRequest()),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('returns existing order for idempotent createOrder', async () => {
    const expiresAt = new Date('2026-04-05T13:00:00Z');
    checkoutIdempotencyFindUnique.mockResolvedValue({
      order: {
        id: 'order-id',
        orderNumber: 'LUM-260405-ABC123',
        status: OrderStatus.pending_payment,
        totalCents: 5494,
        currency: 'GBP',
        mockPaymentSession: { id: 'session-id', expiresAt },
      },
    });

    const result = await service.createOrder(
      null,
      'guest-cart-id',
      'idem-key',
      createOrderRequest(),
    );

    expect(result).toEqual({
      orderId: 'order-id',
      orderNumber: 'LUM-260405-ABC123',
      status: 'pending_payment',
      totalCents: 5494,
      currency: 'GBP',
      mockPaymentSessionId: 'session-id',
      paymentExpiresAt: expiresAt.toISOString(),
    });
    expect(getCartForCheckout).not.toHaveBeenCalled();
  });

  it('creates order and reserves stock', async () => {
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 4999,
      currency: 'GBP',
      items: [
        {
          variantId: 'variant-id',
          productName: 'Lamp',
          variantLabel: 'White',
          sku: 'SKU-1',
          quantity: 1,
          unitPrice: { amountCents: 4999, currency: 'GBP' },
          lineSubtotalCents: 4999,
        },
      ],
    });

    const expiresAt = new Date('2026-04-05T13:00:00Z');
    const productVariantFindUnique = jest.fn().mockResolvedValue({
      id: 'variant-id',
      isActive: true,
      stockQuantity: 5,
      reservedQuantity: 0,
    });
    const productVariantUpdate = jest.fn();
    const orderCreate = jest.fn().mockResolvedValue({
      id: 'order-id',
      orderNumber: 'LUM-260405-ABC123',
      status: OrderStatus.pending_payment,
      totalCents: 5494,
      currency: 'GBP',
      mockPaymentSession: { id: 'session-id', expiresAt },
    });
    const guestCartItemDeleteMany = jest.fn();

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<unknown>) =>
      fn({
        productVariant: {
          findUnique: productVariantFindUnique,
          update: productVariantUpdate,
        },
        order: { create: orderCreate },
        guestCartItem: { deleteMany: guestCartItemDeleteMany },
      }),
    );

    const result = await service.createOrder(
      null,
      'guest-cart-id',
      'idem-key',
      createOrderRequest(),
    );

    expect(productVariantUpdate).toHaveBeenCalledWith({
      where: { id: 'variant-id' },
      data: { reservedQuantity: { increment: 1 } },
    });
    expect(orderCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          items: {
            create: [
              expect.objectContaining({
                productName: 'Lamp',
                variantLabel: 'White',
                sku: 'SKU-1',
                unitPriceCents: 4999,
                lineTotalCents: 4999,
              }),
            ],
          },
        }),
      }),
    );
    expect(result.status).toBe('pending_payment');
    expect(result.mockPaymentSessionId).toBe('session-id');
  });

  it('returns existing order when idempotency insert races (P2002)', async () => {
    const expiresAt = new Date('2026-04-05T13:00:00Z');
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 4999,
      currency: 'GBP',
      items: [
        {
          variantId: 'variant-id',
          productName: 'Lamp',
          variantLabel: 'White',
          sku: 'SKU-1',
          quantity: 1,
          unitPrice: { amountCents: 4999, currency: 'GBP' },
          lineSubtotalCents: 4999,
        },
      ],
    });

    checkoutIdempotencyFindUnique
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce({
        order: {
          id: 'order-id',
          orderNumber: 'LUM-260405-ABC123',
          status: OrderStatus.pending_payment,
          totalCents: 5494,
          currency: 'GBP',
          mockPaymentSession: { id: 'session-id', expiresAt },
        },
      });

    transaction.mockRejectedValue(
      new Prisma.PrismaClientKnownRequestError('Unique constraint', {
        code: 'P2002',
        clientVersion: 'test',
      }),
    );

    const result = await service.createOrder(
      null,
      'guest-cart-id',
      'idem-key',
      createOrderRequest(),
    );

    expect(result.orderId).toBe('order-id');
    expect(checkoutIdempotencyFindUnique).toHaveBeenCalledTimes(2);
  });

  it('throws conflict when stock is insufficient during createOrder', async () => {
    getCartForCheckout.mockResolvedValue({
      subtotalCents: 4999,
      currency: 'GBP',
      items: [
        {
          variantId: 'variant-id',
          productName: 'Lamp',
          variantLabel: 'White',
          sku: 'SKU-1',
          quantity: 3,
          unitPrice: { amountCents: 4999, currency: 'GBP' },
          lineSubtotalCents: 14997,
        },
      ],
    });

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<unknown>) =>
      fn({
        productVariant: {
          findUnique: jest.fn().mockResolvedValue({
            id: 'variant-id',
            isActive: true,
            stockQuantity: 2,
            reservedQuantity: 0,
          }),
        },
      }),
    );

    await expect(
      service.createOrder(null, 'guest-cart-id', 'idem-key', createOrderRequest()),
    ).rejects.toBeInstanceOf(ConflictException);
  });
});
