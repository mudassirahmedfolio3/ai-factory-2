import { OrderStatus } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { DEMO_SHOPPER_EMAIL, OrdersSeedService } from './orders-seed.service';

describe('OrdersSeedService', () => {
  it('seedDemoOrders upserts demo shopper and three lifecycle orders', async () => {
    const variantFindFirst = jest.fn().mockResolvedValue({
      id: 'v1111111-1111-4111-8111-111111111111',
      sku: 'CL-1001-WH',
      label: 'White',
      priceCents: 4999,
      currency: 'GBP',
      product: { name: 'Modern LED Ceiling Light' },
    });
    const userUpsert = jest.fn().mockResolvedValue({
      id: 'u1111111-1111-4111-8111-111111111111',
      email: DEMO_SHOPPER_EMAIL,
    });
    const orderFindUnique = jest
      .fn()
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce(null)
      .mockResolvedValueOnce(null);
    const orderCreate = jest.fn().mockResolvedValue({});
    const orderUpdate = jest.fn();

    const prisma = {
      productVariant: { findFirst: variantFindFirst },
      user: { upsert: userUpsert },
      order: {
        findUnique: orderFindUnique,
        create: orderCreate,
        update: orderUpdate,
      },
    } as unknown as PrismaService;

    const service = new OrdersSeedService(prisma);
    await service.seedDemoOrders();

    expect(userUpsert).toHaveBeenCalledWith(
      expect.objectContaining({ where: { email: DEMO_SHOPPER_EMAIL } }),
    );
    expect(orderCreate).toHaveBeenCalledTimes(3);
    expect(orderCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          status: OrderStatus.fulfilled,
          carrierName: 'Royal Mail',
          trackingNumber: 'RM123456789GB',
        }),
      }),
    );
  });

  it('seedDemoOrders no-ops when catalog variants are missing', async () => {
    const orderCreate = jest.fn();
    const prisma = {
      productVariant: { findFirst: jest.fn().mockResolvedValue(null) },
      order: { create: orderCreate },
    } as unknown as PrismaService;

    await new OrdersSeedService(prisma).seedDemoOrders();
    expect(orderCreate).not.toHaveBeenCalled();
  });
});
