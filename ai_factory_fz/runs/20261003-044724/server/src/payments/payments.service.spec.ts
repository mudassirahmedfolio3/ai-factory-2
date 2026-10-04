import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PaymentsService } from './payments.service.js';

describe('PaymentsService', () => {
  const prisma = {
    payment: {
      create: vi.fn(),
    },
  };

  let service: PaymentsService;

  beforeEach(() => {
    vi.resetAllMocks();
    service = new PaymentsService(prisma as never);
  });

  it('creates a succeeded MOCK payment with mockReference', async () => {
    prisma.payment.create.mockResolvedValue({ id: 'pay-1' });

    await service.createMockPayment('order-1', 2500, 'USD');

    expect(prisma.payment.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          orderId: 'order-1',
          provider: 'MOCK',
          status: 'succeeded',
          amountCents: 2500,
          currency: 'USD',
          mockReference: expect.stringMatching(/^MOCK-[A-F0-9]{8}$/),
        }),
      }),
    );
  });
});
