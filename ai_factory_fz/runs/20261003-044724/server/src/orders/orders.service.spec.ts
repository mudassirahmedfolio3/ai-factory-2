import { ConflictException, NotFoundException } from '@nestjs/common';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OrdersService } from './orders.service.js';

describe('OrdersService', () => {
  const prisma = {
    order: {
      findUnique: vi.fn(),
      findFirst: vi.fn(),
      findMany: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    productVariant: {
      findUnique: vi.fn(),
      update: vi.fn(),
      updateMany: vi.fn(),
    },
    coupon: { update: vi.fn() },
    payment: { create: vi.fn() },
    $transaction: vi.fn(),
  };

  const checkoutService = {
    resolveLinesForOrder: vi.fn(),
    loadStoreConfig: vi.fn(),
    loadCoupon: vi.fn(),
    computeBreakdownForLines: vi.fn(),
  };

  let service: OrdersService;

  beforeEach(() => {
    vi.resetAllMocks();
    prisma.$transaction.mockImplementation(
      async (fn: (tx: typeof prisma) => Promise<unknown>) => fn(prisma),
    );
    service = new OrdersService(prisma as never, checkoutService as never);
  });

  it('returns existing order for duplicate idempotency key', async () => {
    const existing = {
      id: 'ord-1',
      userId: 'user-1',
      orderNumber: 'SE-1',
      status: 'pending_payment',
      currency: 'USD',
      subtotalCents: 100,
      discountCents: 0,
      shippingCents: 0,
      taxCents: 0,
      totalCents: 100,
      couponCode: null,
      shippingAddressSnapshot: { fullName: 'A', line1: '1', city: 'c', region: 'TX', postalCode: '78701', country: 'US' },
      carrierName: null,
      trackingNumber: null,
      createdAt: new Date(),
      items: [],
    };
    prisma.order.findUnique.mockResolvedValue(existing);

    const result = await service.createOrder('user-1', {
      idempotencyKey: 'key-1',
      shippingAddress: existing.shippingAddressSnapshot as never,
    });

    expect(result.id).toBe('ord-1');
    expect(checkoutService.resolveLinesForOrder).not.toHaveBeenCalled();
  });

  it('rejects mock payment when order is not pending', async () => {
    prisma.order.findFirst.mockResolvedValue({
      id: 'ord-2',
      userId: 'user-1',
      status: 'cancelled',
      items: [],
      payment: null,
    });

    await expect(
      service.completeMockPayment('user-1', 'ord-2'),
    ).rejects.toBeInstanceOf(ConflictException);
  });

  it('throws not found for foreign order', async () => {
    prisma.order.findFirst.mockResolvedValue(null);

    await expect(
      service.getOrderById('user-1', 'missing'),
    ).rejects.toBeInstanceOf(NotFoundException);
  });

  it('cancelOrder releases reserved stock for pending_payment orders (US-009)', async () => {
    prisma.order.findFirst.mockResolvedValue({
      id: 'ord-pending',
      userId: 'user-1',
      status: 'pending_payment',
      items: [{ variantId: 'var-1', quantity: 2 }],
    });
    const cancelledAt = new Date();
    prisma.order.update.mockResolvedValue({
      id: 'ord-pending',
      userId: 'user-1',
      orderNumber: 'SE-CANCEL-01',
      status: 'cancelled',
      currency: 'USD',
      subtotalCents: 1000,
      discountCents: 0,
      shippingCents: 599,
      taxCents: 80,
      totalCents: 1679,
      couponCode: null,
      shippingAddressSnapshot: {
        fullName: 'A',
        line1: '1',
        city: 'Austin',
        region: 'TX',
        postalCode: '78701',
        country: 'US',
      },
      carrierName: null,
      trackingNumber: null,
      createdAt: new Date('2026-10-04T00:00:00.000Z'),
      cancelledAt,
      items: [],
    });

    await service.cancelOrder('user-1', 'ord-pending');

    expect(prisma.productVariant.update).toHaveBeenCalledWith({
      where: { id: 'var-1' },
      data: { reservedQuantity: { decrement: 2 } },
    });
    expect(prisma.order.update).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { id: 'ord-pending' },
        data: expect.objectContaining({ status: 'cancelled' }),
      }),
    );
  });
});
