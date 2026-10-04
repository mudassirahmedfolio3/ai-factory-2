import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type { Order, OrderItem } from '@prisma/client';
import { OrderStatus, PaymentProvider, PaymentStatus } from '@prisma/client';
import { randomBytes } from 'node:crypto';
import { PrismaService } from '../prisma/prisma.service.js';
import { CheckoutService } from '../checkout/checkout.service.js';
import { validateUsShippingAddress } from '../checkout/us-address.util.js';
import type { CreateOrderRequestDto, OrderDetailDto } from './dto/orders.dto.js';
import { toOrderDetail, toOrderSummary } from './order.mapper.js';
import type { OrderListResponseDto } from './dto/orders.dto.js';

const PAYMENT_HOLD_MINUTES = 30;

@Injectable()
export class OrdersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly checkoutService: CheckoutService,
  ) {}

  async createOrder(
    userId: string,
    dto: CreateOrderRequestDto,
  ): Promise<OrderDetailDto> {
    const existing = await this.prisma.order.findUnique({
      where: { idempotencyKey: dto.idempotencyKey },
      include: { items: true },
    });
    if (existing !== null) {
      if (existing.userId !== userId) {
        throw new NotFoundException('Order not found');
      }
      return toOrderDetail(existing);
    }

    const addressError = validateUsShippingAddress(dto.shippingAddress);
    if (addressError !== null) {
      throw new BadRequestException(addressError);
    }

    const useServerCart = dto.useServerCart !== false;
    const lines = await this.checkoutService.resolveLinesForOrder(
      userId,
      useServerCart,
      dto.lines,
    );
    if (lines.length === 0) {
      throw new BadRequestException('Cart is empty');
    }

    const storeConfig = await this.checkoutService.loadStoreConfig();
    const couponRecord = await this.checkoutService.loadCoupon(dto.couponCode);
    const breakdown = this.checkoutService.computeBreakdownForLines(
      lines,
      storeConfig,
      couponRecord,
      dto.couponCode,
    );

    const orderNumber = await this.generateOrderNumber();
    const paymentExpiresAt = new Date(
      Date.now() + PAYMENT_HOLD_MINUTES * 60 * 1000,
    );

    const order = await this.prisma.$transaction(async (tx) => {
      for (const line of lines) {
        const variant = await tx.productVariant.findUnique({
          where: { id: line.variantId },
        });
        if (variant === null) {
          throw new BadRequestException(
            'Insufficient stock for one or more items',
          );
        }
        const available =
          variant.stockQuantity - variant.reservedQuantity;
        if (line.quantity > available) {
          throw new BadRequestException(
            'Insufficient stock for one or more items',
          );
        }
        await tx.productVariant.update({
          where: { id: line.variantId },
          data: { reservedQuantity: { increment: line.quantity } },
        });
      }

      const created = await tx.order.create({
        data: {
          userId,
          orderNumber,
          status: OrderStatus.pending_payment,
          currency: breakdown.currency,
          subtotalCents: breakdown.subtotalCents,
          discountCents: breakdown.discountCents,
          shippingCents: breakdown.shippingCents,
          taxCents: breakdown.taxCents,
          totalCents: breakdown.totalCents,
          couponId: breakdown.appliedCouponId,
          couponCode: breakdown.appliedCouponCode,
          shippingAddressSnapshot: { ...dto.shippingAddress },
          idempotencyKey: dto.idempotencyKey,
          paymentExpiresAt,
          items: {
            create: lines.map((line) => ({
              variantId: line.variantId,
              productName: line.productName,
              variantName: line.variantName,
              sku: line.sku,
              quantity: line.quantity,
              unitPriceCents: line.unitPriceCents,
              currency: line.currency,
              lineTotalCents: line.unitPriceCents * line.quantity,
            })),
          },
        },
        include: { items: true },
      });

      if (breakdown.appliedCouponId !== null) {
        await tx.coupon.update({
          where: { id: breakdown.appliedCouponId },
          data: { redemptionCount: { increment: 1 } },
        });
      }

      return created;
    });

    return toOrderDetail(order as Order & { items: OrderItem[] });
  }

  async listOrders(
    userId: string,
    page: number,
    pageSize: number,
  ): Promise<OrderListResponseDto> {
    const skip = (page - 1) * pageSize;
    const [orders, total] = await Promise.all([
      this.prisma.order.findMany({
        where: { userId },
        orderBy: { createdAt: 'desc' },
        skip,
        take: pageSize,
      }),
      this.prisma.order.count({ where: { userId } }),
    ]);

    return {
      items: orders.map(toOrderSummary),
      total,
      page,
      pageSize,
    };
  }

  async getOrderById(userId: string, orderId: string): Promise<OrderDetailDto> {
    const order = await this.prisma.order.findFirst({
      where: { id: orderId, userId },
      include: { items: true },
    });
    if (order === null) {
      throw new NotFoundException('Order not found');
    }
    return toOrderDetail(order);
  }

  async completeMockPayment(
    userId: string,
    orderId: string,
  ): Promise<OrderDetailDto> {
    const order = await this.prisma.order.findFirst({
      where: { id: orderId, userId },
      include: { items: true, payment: true },
    });
    if (order === null) {
      throw new NotFoundException('Order not found');
    }

    if (order.status === OrderStatus.paid) {
      return toOrderDetail(order);
    }

    if (order.status !== OrderStatus.pending_payment) {
      throw new ConflictException('Order is not payable');
    }

    const updated = await this.prisma.$transaction(async (tx) => {
      for (const item of order.items) {
        if (item.variantId === null) {
          continue;
        }
        const result = await tx.productVariant.updateMany({
          where: {
            id: item.variantId,
            stockQuantity: { gte: item.quantity },
            reservedQuantity: { gte: item.quantity },
          },
          data: {
            stockQuantity: { decrement: item.quantity },
            reservedQuantity: { decrement: item.quantity },
          },
        });
        if (result.count !== 1) {
          throw new ConflictException('Order is not payable');
        }
      }

      const paidOrder = await tx.order.update({
        where: { id: order.id },
        data: {
          status: OrderStatus.paid,
          paidAt: new Date(),
        },
        include: { items: true },
      });

      if (order.payment === null) {
        await tx.payment.create({
          data: {
            orderId: order.id,
            provider: PaymentProvider.MOCK,
            status: PaymentStatus.succeeded,
            amountCents: order.totalCents,
            currency: order.currency,
            mockReference: `MOCK-${randomBytes(4).toString('hex').toUpperCase()}`,
          },
        });
      }

      return paidOrder;
    });

    const withItems = await this.prisma.order.findUniqueOrThrow({
      where: { id: updated.id },
      include: { items: true },
    });
    return toOrderDetail(withItems);
  }

  async cancelOrder(userId: string, orderId: string): Promise<OrderDetailDto> {
    const order = await this.prisma.order.findFirst({
      where: { id: orderId, userId },
      include: { items: true },
    });
    if (order === null) {
      throw new NotFoundException('Order not found');
    }

    if (order.status === OrderStatus.cancelled) {
      return toOrderDetail(order);
    }

    if (order.status !== OrderStatus.pending_payment) {
      throw new ConflictException('Order is not cancellable');
    }

    const cancelled = await this.prisma.$transaction(async (tx) => {
      for (const item of order.items) {
        if (item.variantId === null) {
          continue;
        }
        await tx.productVariant.update({
          where: { id: item.variantId },
          data: { reservedQuantity: { decrement: item.quantity } },
        });
      }

      return tx.order.update({
        where: { id: order.id },
        data: {
          status: OrderStatus.cancelled,
          cancelledAt: new Date(),
        },
        include: { items: true },
      });
    });

    return toOrderDetail(cancelled);
  }

  private async generateOrderNumber(): Promise<string> {
    const datePart = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    for (let attempt = 0; attempt < 5; attempt += 1) {
      const suffix = Math.random().toString(36).slice(2, 8).toUpperCase();
      const candidate = `SE-${datePart}-${suffix}`;
      const exists = await this.prisma.order.findUnique({
        where: { orderNumber: candidate },
        select: { id: true },
      });
      if (exists === null) {
        return candidate;
      }
    }
    throw new BadRequestException('Unable to generate order number');
  }
}
