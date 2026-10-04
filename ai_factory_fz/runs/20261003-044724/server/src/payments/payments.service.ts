import { Injectable } from '@nestjs/common';
import { PaymentProvider, PaymentStatus } from '@prisma/client';
import { randomBytes } from 'node:crypto';
import { PrismaService } from '../prisma/prisma.service.js';

@Injectable()
export class PaymentsService {
  constructor(private readonly prisma: PrismaService) {}

  async createMockPayment(
    orderId: string,
    amountCents: number,
    currency: string,
  ): Promise<void> {
    await this.prisma.payment.create({
      data: {
        orderId,
        provider: PaymentProvider.MOCK,
        status: PaymentStatus.succeeded,
        amountCents,
        currency,
        mockReference: `MOCK-${randomBytes(4).toString('hex').toUpperCase()}`,
      },
    });
  }
}
