import { HttpException, NotFoundException } from '@nestjs/common';
import { OrderStatus, PaymentStatus } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { PaymentsService } from './payments.service';

describe('PaymentsService', () => {
  let service: PaymentsService;
  let orderFindUnique: jest.Mock;
  let transaction: jest.Mock;

  const orderId = '11111111-1111-4111-8111-111111111111';
  const sessionId = '22222222-2222-4222-8222-222222222222';

  const baseOrder = {
    id: orderId,
    orderNumber: 'LUM-260405-ABC123',
    userId: null,
    status: OrderStatus.pending_payment,
    paidAt: null,
    mockPaymentSession: {
      id: sessionId,
      expiresAt: new Date(Date.now() + 60_000),
      consumedAt: null,
    },
    payment: { status: PaymentStatus.requires_confirmation },
    items: [
      {
        variantId: '33333333-3333-4333-8333-333333333333',
        quantity: 1,
      },
    ],
    reservations: [
      {
        id: '44444444-4444-4444-8444-444444444444',
        variantId: '33333333-3333-4333-8333-333333333333',
        quantity: 1,
        releasedAt: null,
      },
    ],
  };

  beforeEach(() => {
    orderFindUnique = jest.fn();
    transaction = jest.fn(async (fn: (tx: unknown) => Promise<void>) => fn({}));

    const prisma = {
      order: { findUnique: orderFindUnique },
      $transaction: transaction,
    } as unknown as PrismaService;

    service = new PaymentsService(prisma);
  });

  it('marks order paid on success', async () => {
    orderFindUnique.mockResolvedValue(baseOrder);

    const stockReservationFindMany = jest.fn().mockResolvedValue(baseOrder.reservations);
    const productVariantUpdate = jest.fn();
    const stockReservationUpdate = jest.fn();
    const mockPaymentSessionUpdate = jest.fn();
    const paymentUpdate = jest.fn();
    const orderUpdate = jest.fn();

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        stockReservation: {
          findMany: stockReservationFindMany,
          update: stockReservationUpdate,
        },
        productVariant: { update: productVariantUpdate },
        mockPaymentSession: { update: mockPaymentSessionUpdate },
        payment: { update: paymentUpdate },
        order: { update: orderUpdate },
      }),
    );

    const result = await service.confirmMockPayment(null, {
      orderId,
      mockPaymentSessionId: sessionId,
      outcome: 'success',
    });

    expect(result.status).toBe('paid');
    expect(result.orderNumber).toBe(baseOrder.orderNumber);
    expect(paymentUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ status: PaymentStatus.succeeded }),
      }),
    );
  });

  it('returns 402 on payment failure and releases stock', async () => {
    orderFindUnique.mockResolvedValue(baseOrder);

    const releaseReservations = jest.fn();
    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        stockReservation: {
          findMany: jest.fn().mockResolvedValue(baseOrder.reservations),
          update: jest.fn(),
        },
        productVariant: { update: jest.fn() },
        payment: { update: jest.fn() },
      }),
    );

    await expect(
      service.confirmMockPayment(null, {
        orderId,
        mockPaymentSessionId: sessionId,
        outcome: 'failure',
      }),
    ).rejects.toBeInstanceOf(HttpException);

    expect(transaction).toHaveBeenCalled();
    void releaseReservations;
  });

  it('cancels order and releases stock on cancel outcome', async () => {
    orderFindUnique.mockResolvedValue(baseOrder);

    const stockReservationFindMany = jest.fn().mockResolvedValue(baseOrder.reservations);
    const stockReservationUpdate = jest.fn();
    const productVariantUpdate = jest.fn();
    const mockPaymentSessionUpdate = jest.fn();
    const paymentUpdate = jest.fn();
    const orderUpdate = jest.fn();

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        stockReservation: {
          findMany: stockReservationFindMany,
          update: stockReservationUpdate,
        },
        productVariant: { update: productVariantUpdate },
        mockPaymentSession: { update: mockPaymentSessionUpdate },
        payment: { update: paymentUpdate },
        order: { update: orderUpdate },
      }),
    );

    const result = await service.confirmMockPayment(null, {
      orderId,
      mockPaymentSessionId: sessionId,
      outcome: 'cancel',
    });

    expect(result.status).toBe('cancelled');
    expect(productVariantUpdate).toHaveBeenCalledWith({
      where: { id: baseOrder.items[0].variantId },
      data: { reservedQuantity: { decrement: 1 } },
    });
    expect(orderUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ status: OrderStatus.cancelled }),
      }),
    );
  });

  it('is idempotent when order is already paid', async () => {
    const paidAt = new Date('2026-04-05T12:00:00Z');
    orderFindUnique.mockResolvedValue({
      ...baseOrder,
      status: OrderStatus.paid,
      paidAt,
    });

    const result = await service.confirmMockPayment(null, {
      orderId,
      mockPaymentSessionId: sessionId,
      outcome: 'success',
    });

    expect(result.status).toBe('paid');
    expect(transaction).not.toHaveBeenCalled();
  });

  it('rejects invalid session', async () => {
    orderFindUnique.mockResolvedValue({
      ...baseOrder,
      mockPaymentSession: {
        ...baseOrder.mockPaymentSession,
        id: 'wrong-session',
      },
    });

    await expect(
      service.confirmMockPayment(null, {
        orderId,
        mockPaymentSessionId: sessionId,
        outcome: 'success',
      }),
    ).rejects.toBeInstanceOf(NotFoundException);
  });
});
