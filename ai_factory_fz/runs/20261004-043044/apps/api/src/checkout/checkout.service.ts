import {
  BadRequestException,
  ConflictException,
  Injectable,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { OrderStatus, PaymentStatus, Prisma } from '@prisma/client';
import { INSUFFICIENT_STOCK_MESSAGE } from '../cart/cart.constants';
import { CartService } from '../cart/cart.service';
import { PrismaService } from '../prisma/prisma.service';
import { CheckoutCouponService } from './checkout-coupon.service';
import {
  DEFAULT_MOCK_PAYMENT_SESSION_EXPIRES_SECONDS,
  DEFAULT_STOCK_RESERVATION_EXPIRES_SECONDS,
  DEFAULT_UK_FREE_DELIVERY_THRESHOLD_CENTS,
  DEFAULT_UK_SHIPPING_FLAT_RATE_CENTS,
  IDEMPOTENCY_KEY_REQUIRED_MESSAGE,
  IDEMPOTENCY_KEY_TOO_LONG_MESSAGE,
  INVALID_CHECKOUT_MESSAGE,
  INVALID_UK_ADDRESS_MESSAGE,
} from './checkout.constants';
import {
  calculateCheckoutTotalCents,
  calculateUkShippingQuote,
} from './checkout-shipping';
import { CheckoutPreviewRequestDto } from './dto/checkout-preview-request.dto';
import { CheckoutPreviewResponseDto } from './dto/checkout-preview-response.dto';
import { CreateOrderRequestDto } from './dto/create-order-request.dto';
import { CreateOrderResponseDto } from './dto/create-order-response.dto';
import { generateOrderNumber } from './order-number.util';
import { assertMainlandUkAddress } from './uk-address.validation';

@Injectable()
export class CheckoutService {
  private readonly flatRateCents: number;
  private readonly freeDeliveryThresholdCents: number;
  private readonly mockPaymentSessionExpiresSeconds: number;
  private readonly stockReservationExpiresSeconds: number;

  constructor(
    private readonly cartService: CartService,
    private readonly checkoutCouponService: CheckoutCouponService,
    private readonly prisma: PrismaService,
    configService: ConfigService,
  ) {
    this.flatRateCents =
      configService.get<number>('UK_SHIPPING_FLAT_RATE_CENTS') ??
      DEFAULT_UK_SHIPPING_FLAT_RATE_CENTS;
    this.freeDeliveryThresholdCents =
      configService.get<number>('UK_FREE_DELIVERY_THRESHOLD_CENTS') ??
      DEFAULT_UK_FREE_DELIVERY_THRESHOLD_CENTS;
    this.mockPaymentSessionExpiresSeconds =
      configService.get<number>('MOCK_PAYMENT_SESSION_EXPIRES_SECONDS') ??
      DEFAULT_MOCK_PAYMENT_SESSION_EXPIRES_SECONDS;
    this.stockReservationExpiresSeconds =
      configService.get<number>('STOCK_RESERVATION_EXPIRES_SECONDS') ??
      DEFAULT_STOCK_RESERVATION_EXPIRES_SECONDS;
  }

  async previewCheckout(
    userId: string | null,
    guestCartIdHeader: string | undefined,
    dto: CheckoutPreviewRequestDto,
  ): Promise<CheckoutPreviewResponseDto> {
    try {
      assertMainlandUkAddress(dto.shippingAddress);
    } catch {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_UK_ADDRESS_MESSAGE,
      });
    }

    const cart = await this.cartService.getCartForCheckout(userId, guestCartIdHeader);
    const subtotalCents = cart.subtotalCents;
    const currency = cart.currency;

    const shipping = calculateUkShippingQuote(
      subtotalCents,
      this.flatRateCents,
      this.freeDeliveryThresholdCents,
    );

    let discountCents = 0;
    let couponApplied = false;
    let couponCode: string | undefined;
    let couponMessage: string | undefined;

    if (dto.couponCode?.trim()) {
      const couponPreview = await this.checkoutCouponService.resolveCouponPreview(
        dto.couponCode,
        subtotalCents,
        currency,
        cart.items,
        userId,
      );
      couponApplied = couponPreview.couponApplied;
      couponCode = couponPreview.couponCode;
      couponMessage = couponPreview.couponMessage;
      discountCents = couponPreview.discountCents;
    }

    const totalCents = calculateCheckoutTotalCents(
      subtotalCents,
      shipping.shippingCents,
      discountCents,
    );

    return {
      subtotalCents,
      shippingCents: shipping.shippingCents,
      discountCents,
      totalCents,
      currency,
      shippingLabel: shipping.shippingLabel,
      freeDeliveryThresholdCents: shipping.freeDeliveryThresholdCents,
      couponApplied,
      ...(couponCode ? { couponCode } : {}),
      ...(couponMessage ? { couponMessage } : {}),
    };
  }

  async createOrder(
    userId: string | null,
    guestCartIdHeader: string | undefined,
    idempotencyKey: string | undefined,
    dto: CreateOrderRequestDto,
  ): Promise<CreateOrderResponseDto> {
    this.assertIdempotencyKey(idempotencyKey);

    try {
      assertMainlandUkAddress(dto.shippingAddress);
    } catch {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_UK_ADDRESS_MESSAGE,
      });
    }

    const existing = await this.prisma.checkoutIdempotency.findUnique({
      where: { idempotencyKey: idempotencyKey! },
      include: {
        order: { include: { mockPaymentSession: true } },
      },
    });

    if (existing?.order) {
      return this.toCreateOrderResponse(existing.order);
    }

    const cart = await this.cartService.getCartForCheckout(userId, guestCartIdHeader);
    const subtotalCents = cart.subtotalCents;
    const currency = cart.currency;

    const shipping = calculateUkShippingQuote(
      subtotalCents,
      this.flatRateCents,
      this.freeDeliveryThresholdCents,
    );

    let discountCents = 0;
    let couponId: string | undefined;

    if (dto.couponCode?.trim()) {
      const couponPreview = await this.checkoutCouponService.resolveCouponPreview(
        dto.couponCode,
        subtotalCents,
        currency,
        cart.items,
        userId,
      );
      discountCents = couponPreview.discountCents;
      if (couponPreview.couponApplied && couponPreview.couponCode) {
        const coupon = await this.prisma.coupon.findFirst({
          where: { code: { equals: couponPreview.couponCode, mode: 'insensitive' } },
          select: { id: true },
        });
        couponId = coupon?.id;
      }
    }

    const totalCents = calculateCheckoutTotalCents(
      subtotalCents,
      shipping.shippingCents,
      discountCents,
    );

    const reservationExpiresAt = new Date(
      Date.now() + this.stockReservationExpiresSeconds * 1000,
    );
    const paymentExpiresAt = new Date(
      Date.now() + this.mockPaymentSessionExpiresSeconds * 1000,
    );
    const addressSnapshot = dto.shippingAddress as unknown as Prisma.InputJsonValue;
    const guestEmail = userId ? null : dto.contactEmail.trim().toLowerCase();

    try {
      const order = await this.prisma.$transaction(async (tx) => {
        for (const line of cart.items) {
          const variant = await tx.productVariant.findUnique({
            where: { id: line.variantId },
          });
          if (!variant || !variant.isActive) {
            throw new ConflictException({
              statusCode: 409,
              error: 'Conflict',
              message: INSUFFICIENT_STOCK_MESSAGE,
            });
          }
          const available = variant.stockQuantity - variant.reservedQuantity;
          if (line.quantity > available) {
            throw new ConflictException({
              statusCode: 409,
              error: 'Conflict',
              message: INSUFFICIENT_STOCK_MESSAGE,
            });
          }
          await tx.productVariant.update({
            where: { id: variant.id },
            data: { reservedQuantity: { increment: line.quantity } },
          });
        }

        const created = await tx.order.create({
          data: {
            orderNumber: generateOrderNumber(),
            userId: userId ?? undefined,
            guestEmail: guestEmail ?? undefined,
            status: OrderStatus.pending_payment,
            currency,
            subtotalCents,
            discountCents,
            shippingCents: shipping.shippingCents,
            totalCents,
            couponId,
            shippingAddressSnapshot: addressSnapshot,
            idempotencyKey: idempotencyKey!,
            items: {
              create: cart.items.map((line) => ({
                variantId: line.variantId,
                productName: line.productName,
                variantLabel: line.variantLabel,
                sku: line.sku,
                quantity: line.quantity,
                unitPriceCents: line.unitPrice.amountCents,
                currency: line.unitPrice.currency,
                lineTotalCents: line.lineSubtotalCents,
              })),
            },
            reservations: {
              create: cart.items.map((line) => ({
                variantId: line.variantId,
                quantity: line.quantity,
                expiresAt: reservationExpiresAt,
              })),
            },
            payment: {
              create: {
                provider: 'mock',
                status: PaymentStatus.requires_confirmation,
                amountCents: totalCents,
                currency,
              },
            },
            mockPaymentSession: {
              create: { expiresAt: paymentExpiresAt },
            },
            checkoutIdempotency: {
              create: { idempotencyKey: idempotencyKey! },
            },
          },
          include: {
            mockPaymentSession: true,
            items: true,
          },
        });

        if (couponId) {
          await tx.couponRedemption.create({
            data: {
              couponId,
              orderId: created.id,
              email: dto.contactEmail.trim().toLowerCase(),
            },
          });
        }

        if (userId) {
          await tx.cartItem.deleteMany({ where: { cart: { userId } } });
        } else if (guestCartIdHeader) {
          await tx.guestCartItem.deleteMany({ where: { guestCartId: guestCartIdHeader } });
        }

        return created;
      });

      return this.toCreateOrderResponse(order);
    } catch (error) {
      if (error instanceof ConflictException || error instanceof BadRequestException) {
        throw error;
      }
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        error.code === 'P2002'
      ) {
        const raced = await this.prisma.checkoutIdempotency.findUnique({
          where: { idempotencyKey: idempotencyKey! },
          include: {
            order: { include: { mockPaymentSession: true } },
          },
        });
        if (raced?.order) {
          return this.toCreateOrderResponse(raced.order);
        }
      }
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_CHECKOUT_MESSAGE,
      });
    }
  }

  private assertIdempotencyKey(idempotencyKey: string | undefined): void {
    if (!idempotencyKey) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: IDEMPOTENCY_KEY_REQUIRED_MESSAGE,
      });
    }
    if (idempotencyKey.length > 64) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: IDEMPOTENCY_KEY_TOO_LONG_MESSAGE,
      });
    }
  }

  private toCreateOrderResponse(
    order: {
      id: string;
      orderNumber: string;
      status: OrderStatus;
      totalCents: number;
      currency: string;
      mockPaymentSession: { id: string; expiresAt: Date } | null;
    },
  ): CreateOrderResponseDto {
    if (!order.mockPaymentSession) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_CHECKOUT_MESSAGE,
      });
    }

    return {
      orderId: order.id,
      orderNumber: order.orderNumber,
      status: 'pending_payment',
      totalCents: order.totalCents,
      currency: order.currency,
      mockPaymentSessionId: order.mockPaymentSession.id,
      paymentExpiresAt: order.mockPaymentSession.expiresAt.toISOString(),
    };
  }
}
