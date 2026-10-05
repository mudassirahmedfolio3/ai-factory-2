import {
  HttpException,
  HttpStatus,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { OrderStatus, PaymentStatus, Prisma } from '@prisma/client';
import { INSUFFICIENT_STOCK_MESSAGE } from '../cart/cart.constants';
import { PrismaService } from '../prisma/prisma.service';
import { MockPaymentConfirmRequestDto } from './dto/mock-payment-confirm-request.dto';
import { MockPaymentConfirmResponseDto } from './dto/mock-payment-confirm-response.dto';
import {
  MOCK_PAYMENT_FAILED_MESSAGE,
  MOCK_PAYMENT_ORDER_NOT_FOUND_MESSAGE,
  MOCK_PAYMENT_SESSION_INVALID_MESSAGE,
} from './payments.constants';

type TransactionClient = Prisma.TransactionClient;

@Injectable()
export class PaymentsService {
  constructor(private readonly prisma: PrismaService) {}

  async confirmMockPayment(
    userId: string | null,
    dto: MockPaymentConfirmRequestDto,
  ): Promise<MockPaymentConfirmResponseDto> {
    const order = await this.prisma.order.findUnique({
      where: { id: dto.orderId },
      include: {
        mockPaymentSession: true,
        payment: true,
        items: true,
        reservations: true,
      },
    });

    if (!order) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: MOCK_PAYMENT_ORDER_NOT_FOUND_MESSAGE,
      });
    }

    if (userId && order.userId && order.userId !== userId) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: MOCK_PAYMENT_ORDER_NOT_FOUND_MESSAGE,
      });
    }

    if (order.status === OrderStatus.paid) {
      return this.toPaidResponse(order);
    }

    if (order.status === OrderStatus.cancelled) {
      return {
        orderId: order.id,
        orderNumber: order.orderNumber,
        status: 'cancelled',
        paidAt: order.paidAt?.toISOString() ?? new Date(0).toISOString(),
      };
    }

    const session = order.mockPaymentSession;
    if (
      !session ||
      session.id !== dto.mockPaymentSessionId ||
      session.consumedAt != null ||
      session.expiresAt <= new Date()
    ) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: MOCK_PAYMENT_SESSION_INVALID_MESSAGE,
      });
    }

    if (dto.outcome === 'failure') {
      await this.prisma.$transaction(async (tx) => {
        await this.releaseActiveReservations(tx, order.id, new Date());
        await tx.payment.update({
          where: { orderId: order.id },
          data: { status: PaymentStatus.failed },
        });
      });

      throw new HttpException(
        {
          statusCode: HttpStatus.PAYMENT_REQUIRED,
          error: 'Payment Required',
          message: MOCK_PAYMENT_FAILED_MESSAGE,
        },
        HttpStatus.PAYMENT_REQUIRED,
      );
    }

    if (dto.outcome === 'cancel') {
      const now = new Date();
      await this.prisma.$transaction(async (tx) => {
        await this.releaseActiveReservations(tx, order.id, now);
        await tx.mockPaymentSession.update({
          where: { id: session.id },
          data: { consumedAt: now },
        });
        await tx.payment.update({
          where: { orderId: order.id },
          data: { status: PaymentStatus.canceled, mockSessionId: session.id },
        });
        await tx.order.update({
          where: { id: order.id },
          data: { status: OrderStatus.cancelled, cancelledAt: now },
        });
      });

      return {
        orderId: order.id,
        orderNumber: order.orderNumber,
        status: 'cancelled',
        paidAt: now.toISOString(),
      };
    }

    const paidAt = new Date();
    await this.prisma.$transaction(async (tx) => {
      await this.ensureActiveReservations(tx, order, session.expiresAt);
      const activeReservations = await tx.stockReservation.findMany({
        where: { orderId: order.id, releasedAt: null },
      });

      for (const reservation of activeReservations) {
        await tx.productVariant.update({
          where: { id: reservation.variantId },
          data: {
            stockQuantity: { decrement: reservation.quantity },
            reservedQuantity: { decrement: reservation.quantity },
          },
        });
        await tx.stockReservation.update({
          where: { id: reservation.id },
          data: { releasedAt: paidAt },
        });
      }

      await tx.mockPaymentSession.update({
        where: { id: session.id },
        data: { consumedAt: paidAt },
      });

      await tx.payment.update({
        where: { orderId: order.id },
        data: {
          status: PaymentStatus.succeeded,
          mockSessionId: session.id,
        },
      });

      await tx.order.update({
        where: { id: order.id },
        data: {
          status: OrderStatus.paid,
          paidAt,
        },
      });
    });

    return {
      orderId: order.id,
      orderNumber: order.orderNumber,
      status: 'paid',
      paidAt: paidAt.toISOString(),
    };
  }

  private async ensureActiveReservations(
    tx: TransactionClient,
    order: {
      id: string;
      items: {
        variantId: string | null;
        quantity: number;
      }[];
    },
    reservationExpiresAt: Date,
  ): Promise<void> {
    const active = await tx.stockReservation.findMany({
      where: { orderId: order.id, releasedAt: null },
    });
    if (active.length > 0) {
      return;
    }

    for (const line of order.items) {
      if (!line.variantId) {
        continue;
      }
      const variant = await tx.productVariant.findUnique({
        where: { id: line.variantId },
      });
      if (!variant) {
        throw new HttpException(
          {
            statusCode: HttpStatus.PAYMENT_REQUIRED,
            error: 'Payment Required',
            message: INSUFFICIENT_STOCK_MESSAGE,
          },
          HttpStatus.PAYMENT_REQUIRED,
        );
      }
      const available = variant.stockQuantity - variant.reservedQuantity;
      if (line.quantity > available) {
        throw new HttpException(
          {
            statusCode: HttpStatus.PAYMENT_REQUIRED,
            error: 'Payment Required',
            message: INSUFFICIENT_STOCK_MESSAGE,
          },
          HttpStatus.PAYMENT_REQUIRED,
        );
      }
      await tx.productVariant.update({
        where: { id: variant.id },
        data: { reservedQuantity: { increment: line.quantity } },
      });
      await tx.stockReservation.create({
        data: {
          orderId: order.id,
          variantId: line.variantId,
          quantity: line.quantity,
          expiresAt: reservationExpiresAt,
        },
      });
    }
  }

  private async releaseActiveReservations(
    tx: TransactionClient,
    orderId: string,
    releasedAt: Date,
  ): Promise<void> {
    const reservations = await tx.stockReservation.findMany({
      where: { orderId, releasedAt: null },
    });

    for (const reservation of reservations) {
      await tx.productVariant.update({
        where: { id: reservation.variantId },
        data: { reservedQuantity: { decrement: reservation.quantity } },
      });
      await tx.stockReservation.update({
        where: { id: reservation.id },
        data: { releasedAt },
      });
    }
  }

  private toPaidResponse(order: {
    id: string;
    orderNumber: string;
    paidAt: Date | null;
  }): MockPaymentConfirmResponseDto {
    return {
      orderId: order.id,
      orderNumber: order.orderNumber,
      status: 'paid',
      paidAt: (order.paidAt ?? new Date()).toISOString(),
    };
  }
}
