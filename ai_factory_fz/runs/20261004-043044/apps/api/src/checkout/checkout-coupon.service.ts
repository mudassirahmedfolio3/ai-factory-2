import { BadRequestException, Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { CartLineItemDto } from '../cart/dto/cart-line-item.dto';
import {
  COUPON_ALREADY_USED_MESSAGE,
  COUPON_CURRENCY_MISMATCH_MESSAGE,
  COUPON_EXPIRED_MESSAGE,
  COUPON_INACTIVE_MESSAGE,
  COUPON_NOT_FOUND_MESSAGE,
} from './checkout.constants';
import {
  computeCouponDiscountCents,
  CouponValidationError,
  isCouponExpired,
  parseCouponCodeInput,
} from './checkout-coupon';
import { AppliedCouponPreview, CheckoutCouponLine, LoadedCoupon } from './checkout-coupon.types';

@Injectable()
export class CheckoutCouponService {
  constructor(private readonly prisma: PrismaService) {}

  async resolveCouponPreview(
    couponCodeRaw: string,
    cartSubtotalCents: number,
    currency: string,
    lines: CartLineItemDto[],
    userId: string | null,
  ): Promise<AppliedCouponPreview> {
    let normalizedCodes: string[];
    try {
      normalizedCodes = parseCouponCodeInput(couponCodeRaw);
    } catch (error) {
      if (error instanceof CouponValidationError) {
        throw this.badCouponRequest(error.clientMessage);
      }
      throw error;
    }

    const code = normalizedCodes[0]!;
    const coupon = await this.loadCouponByCode(code);
    if (!coupon) {
      throw this.badCouponRequest(COUPON_NOT_FOUND_MESSAGE);
    }

    if (!coupon.isActive) {
      throw this.badCouponRequest(COUPON_INACTIVE_MESSAGE);
    }

    if (isCouponExpired(coupon.expiresAt, new Date())) {
      throw this.badCouponRequest(COUPON_EXPIRED_MESSAGE);
    }

    if (coupon.currency !== currency) {
      throw this.badCouponRequest(COUPON_CURRENCY_MISMATCH_MESSAGE);
    }

    if (coupon.singleUsePerEmail && userId) {
      const user = await this.prisma.user.findUnique({
        where: { id: userId },
        select: { email: true },
      });
      if (user) {
        const prior = await this.prisma.couponRedemption.findFirst({
          where: { couponId: coupon.id, email: user.email },
        });
        if (prior) {
          throw this.badCouponRequest(COUPON_ALREADY_USED_MESSAGE);
        }
      }
    }

    const couponLines = await this.buildCouponLines(lines);

    try {
      return computeCouponDiscountCents(cartSubtotalCents, couponLines, coupon);
    } catch (error) {
      if (error instanceof CouponValidationError) {
        throw this.badCouponRequest(error.clientMessage);
      }
      throw error;
    }
  }

  private badCouponRequest(message: string): BadRequestException {
    return new BadRequestException({
      statusCode: 400,
      error: 'Bad Request',
      message,
    });
  }

  private async loadCouponByCode(code: string): Promise<LoadedCoupon | null> {
    const row = await this.prisma.coupon.findFirst({
      where: { code: { equals: code, mode: 'insensitive' } },
      include: {
        categories: { select: { categoryId: true } },
        products: { select: { productId: true } },
      },
    });

    if (!row) {
      return null;
    }

    return {
      id: row.id,
      code: row.code,
      description: row.description,
      percentOff: row.percentOff,
      amountOffCents: row.amountOffCents,
      currency: row.currency,
      minSubtotalCents: row.minSubtotalCents,
      expiresAt: row.expiresAt,
      singleUsePerEmail: row.singleUsePerEmail,
      excludeSaleItems: row.excludeSaleItems,
      isActive: row.isActive,
      categoryIds: row.categories.map((entry) => entry.categoryId),
      productIds: row.products.map((entry) => entry.productId),
    };
  }

  private async buildCouponLines(lines: CartLineItemDto[]): Promise<CheckoutCouponLine[]> {
    if (lines.length === 0) {
      return [];
    }

    const variantIds = lines.map((line) => line.variantId);
    const variants = await this.prisma.productVariant.findMany({
      where: { id: { in: variantIds } },
      select: {
        id: true,
        compareAtCents: true,
        product: { select: { id: true, categoryId: true } },
      },
    });
    const variantById = new Map(variants.map((variant) => [variant.id, variant]));

    return lines.map((line) => {
      const variant = variantById.get(line.variantId);
      const unitPriceCents = line.unitPrice.amountCents;
      const compareAtCents = variant?.compareAtCents ?? null;
      const isOnSale = compareAtCents != null && compareAtCents > unitPriceCents;

      return {
        productId: line.productId,
        variantId: line.variantId,
        lineSubtotalCents: line.lineSubtotalCents,
        categoryId: variant?.product.categoryId ?? '',
        isOnSale,
      };
    });
  }
}
