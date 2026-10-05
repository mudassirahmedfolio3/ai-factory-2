import { NotFoundException } from '@nestjs/common';
import { OrderStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { ORDER_NOT_FOUND_MESSAGE } from './orders.constants';
import { OrdersService } from './orders.service';

const userId = '11111111-1111-4111-8111-111111111111';
const orderId = '22222222-2222-4222-8222-222222222222';

describe('OrdersService', () => {
  let service: OrdersService;
  let orderCount: jest.Mock;
  let orderFindMany: jest.Mock;
  let orderFindFirst: jest.Mock;

  beforeEach(() => {
    orderCount = jest.fn();
    orderFindMany = jest.fn();
    orderFindFirst = jest.fn();

    const prisma = {
      order: {
        count: orderCount,
        findMany: orderFindMany,
        findFirst: orderFindFirst,
      },
    } as unknown as PrismaService;

    service = new OrdersService(prisma);
  });

  it('listOrders returns paginated summaries for the signed-in user', async () => {
    orderCount.mockResolvedValue(1);
    orderFindMany.mockResolvedValue([
      {
        id: orderId,
        orderNumber: 'LUM-260405-DEMO01',
        status: OrderStatus.paid,
        totalCents: 5494,
        currency: 'GBP',
        createdAt: new Date('2026-10-01T09:00:00.000Z'),
      },
    ]);

    const result = await service.listOrders(userId, { page: 1, pageSize: 20 });

    expect(orderFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { userId },
        skip: 0,
        take: 20,
        orderBy: { createdAt: Prisma.SortOrder.desc },
      }),
    );
    expect(result.total).toBe(1);
    expect(result.items[0].customerStatusLabel).toBe('Processing');
  });

  it('getOrderById returns detail when the order belongs to the user', async () => {
    orderFindFirst.mockResolvedValue({
      id: orderId,
      orderNumber: 'LUM-260405-DEMO01',
      userId,
      guestEmail: null,
      status: OrderStatus.delivered,
      currency: 'GBP',
      subtotalCents: 4999,
      discountCents: 0,
      shippingCents: 0,
      vatCents: 0,
      totalCents: 4999,
      deliveryOption: 'STANDARD',
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
      carrierName: 'DPD',
      trackingNumber: 'DPD998877',
      paidAt: new Date('2026-10-01T10:00:00.000Z'),
      fulfilledAt: new Date('2026-10-02T10:00:00.000Z'),
      deliveredAt: new Date('2026-10-04T10:00:00.000Z'),
      cancelledAt: null,
      createdAt: new Date('2026-10-01T09:00:00.000Z'),
      updatedAt: new Date('2026-10-04T10:00:00.000Z'),
      items: [],
    });

    const result = await service.getOrderById(userId, orderId);

    expect(orderFindFirst).toHaveBeenCalledWith({
      where: { id: orderId, userId },
      include: { items: { orderBy: { createdAt: Prisma.SortOrder.asc } } },
    });
    expect(result.status).toBe(OrderStatus.delivered);
    expect(result.tracking.carrierName).toBe('DPD');
  });

  it('getOrderById throws NotFound when missing or owned by another user', async () => {
    orderFindFirst.mockResolvedValue(null);

    await expect(service.getOrderById(userId, orderId)).rejects.toMatchObject({
      response: {
        statusCode: 404,
        message: ORDER_NOT_FOUND_MESSAGE,
      },
    });
    await expect(service.getOrderById(userId, orderId)).rejects.toBeInstanceOf(
      NotFoundException,
    );
  });
});
