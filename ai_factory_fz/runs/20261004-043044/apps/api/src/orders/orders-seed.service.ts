import { Injectable } from '@nestjs/common';
import { OrderStatus, PaymentStatus, Prisma } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import { PrismaService } from '../prisma/prisma.service';

export const DEMO_SHOPPER_EMAIL = 'shopper@example.com';
export const DEMO_SHOPPER_PASSWORD = 'Password1!';

const DEMO_ORDER_NUMBERS = {
  processing: 'LUM-260401-DEMO01',
  shipped: 'LUM-260402-DEMO02',
  delivered: 'LUM-260403-DEMO03',
} as const;

const demoShippingAddress = {
  fullName: 'Alex Shopper',
  line1: '10 High Street',
  city: 'London',
  postalCode: 'SW1A 1AA',
  country: 'GB',
} satisfies Prisma.InputJsonObject;

@Injectable()
export class OrdersSeedService {
  constructor(private readonly prisma: PrismaService) {}

  async seedDemoOrders(): Promise<void> {
    const variant = await this.prisma.productVariant.findFirst({
      where: { isActive: true },
      include: { product: true },
      orderBy: { sku: 'asc' },
    });
    if (!variant) {
      return;
    }

    const passwordHash = await bcrypt.hash(DEMO_SHOPPER_PASSWORD, 12);
    const user = await this.prisma.user.upsert({
      where: { email: DEMO_SHOPPER_EMAIL },
      create: {
        email: DEMO_SHOPPER_EMAIL,
        passwordHash,
        displayName: 'Alex Shopper',
      },
      update: {},
    });

    await this.upsertDemoOrder({
      orderNumber: DEMO_ORDER_NUMBERS.processing,
      userId: user.id,
      status: OrderStatus.paid,
      carrierName: null,
      trackingNumber: null,
      paidAt: new Date('2026-09-28T10:00:00.000Z'),
      fulfilledAt: null,
      deliveredAt: null,
      variant,
    });

    await this.upsertDemoOrder({
      orderNumber: DEMO_ORDER_NUMBERS.shipped,
      userId: user.id,
      status: OrderStatus.fulfilled,
      carrierName: 'Royal Mail',
      trackingNumber: 'RM123456789GB',
      paidAt: new Date('2026-09-25T10:00:00.000Z'),
      fulfilledAt: new Date('2026-09-27T14:00:00.000Z'),
      deliveredAt: null,
      variant,
    });

    await this.upsertDemoOrder({
      orderNumber: DEMO_ORDER_NUMBERS.delivered,
      userId: user.id,
      status: OrderStatus.delivered,
      carrierName: 'DPD',
      trackingNumber: 'DPD9988776655',
      paidAt: new Date('2026-09-20T10:00:00.000Z'),
      fulfilledAt: new Date('2026-09-22T09:00:00.000Z'),
      deliveredAt: new Date('2026-09-24T16:30:00.000Z'),
      variant,
    });
  }

  private async upsertDemoOrder(params: {
    orderNumber: string;
    userId: string;
    status: OrderStatus;
    carrierName: string | null;
    trackingNumber: string | null;
    paidAt: Date;
    fulfilledAt: Date | null;
    deliveredAt: Date | null;
    variant: {
      id: string;
      sku: string;
      label: string;
      priceCents: number;
      currency: string;
      product: { name: string };
    };
  }): Promise<void> {
    const lineTotalCents = params.variant.priceCents;
    const shippingCents = lineTotalCents >= 7500 ? 0 : 495;
    const subtotalCents = lineTotalCents;
    const totalCents = subtotalCents + shippingCents;

    const existing = await this.prisma.order.findUnique({
      where: { orderNumber: params.orderNumber },
    });
    if (existing) {
      await this.prisma.order.update({
        where: { id: existing.id },
        data: {
          userId: params.userId,
          status: params.status,
          carrierName: params.carrierName,
          trackingNumber: params.trackingNumber,
          paidAt: params.paidAt,
          fulfilledAt: params.fulfilledAt,
          deliveredAt: params.deliveredAt,
          shippingAddressSnapshot: demoShippingAddress,
        },
      });
      return;
    }

    await this.prisma.order.create({
      data: {
        orderNumber: params.orderNumber,
        userId: params.userId,
        status: params.status,
        currency: params.variant.currency,
        subtotalCents,
        discountCents: 0,
        shippingCents,
        vatCents: 0,
        totalCents,
        shippingAddressSnapshot: demoShippingAddress,
        carrierName: params.carrierName,
        trackingNumber: params.trackingNumber,
        paidAt: params.paidAt,
        fulfilledAt: params.fulfilledAt,
        deliveredAt: params.deliveredAt,
        items: {
          create: [
            {
              variantId: params.variant.id,
              productName: params.variant.product.name,
              variantLabel: params.variant.label,
              sku: params.variant.sku,
              quantity: 1,
              unitPriceCents: params.variant.priceCents,
              currency: params.variant.currency,
              lineTotalCents,
            },
          ],
        },
        payment: {
          create: {
            provider: 'mock',
            status: PaymentStatus.succeeded,
            amountCents: totalCents,
            currency: params.variant.currency,
          },
        },
      },
    });
  }
}
