import { Injectable } from '@nestjs/common';
import type { Coupon, CouponExclusion, StoreConfig } from '@prisma/client';
import { CouponExclusionKind, CouponType } from '@prisma/client';
import type { CartItemResponseDto } from '../cart/dto/cart.dto.js';
import { toCartItemResponse } from '../cart/cart.mapper.js';
import type { CartItem } from '@prisma/client';
import {
  CouponRejectionReason,
  type CouponValidationDto,
} from './dto/checkout.dto.js';

export type PricedLineContext = {
  variantId: string;
  productId: string;
  categoryId: string;
  quantity: number;
  unitPriceCents: number;
  currency: string;
  productName: string;
  variantName: string;
  sku: string;
};

export type PricingBreakdown = {
  lines: CartItemResponseDto[];
  subtotalCents: number;
  discountCents: number;
  shippingCents: number;
  taxCents: number;
  totalCents: number;
  currency: string;
  coupon: CouponValidationDto;
  appliedCouponId: string | null;
  appliedCouponCode: string | null;
};

type CouponWithExclusions = Coupon & { exclusions: CouponExclusion[] };

@Injectable()
export class CheckoutPricingService {
  readonly taxDisclaimer =
    'Estimated tax; final amount may vary based on jurisdiction.';

  buildLineResponses(
    lines: PricedLineContext[],
    syntheticIds: boolean,
  ): CartItemResponseDto[] {
    return lines.map((line, index) => {
      const pseudoItem = {
        id: line.variantId,
        cartId: 'quote',
        variantId: line.variantId,
        quantity: line.quantity,
        unitPriceCents: line.unitPriceCents,
        currency: line.currency,
        productName: line.productName,
        variantName: line.variantName,
        createdAt: new Date(),
        updatedAt: new Date(),
        variant: { productId: line.productId },
      } satisfies CartItem & { variant: { productId: string } };
      return toCartItemResponse(pseudoItem);
    });
  }

  computeBreakdown(
    lines: PricedLineContext[],
    storeConfig: StoreConfig,
    couponRecord: CouponWithExclusions | null,
    couponCodeInput: string | undefined,
    options?: { syntheticLineIds?: boolean },
  ): PricingBreakdown {
    const currency = lines[0]?.currency ?? storeConfig.currency;
    const lineResponses = this.buildLineResponses(
      lines,
      options?.syntheticLineIds ?? true,
    );
    const subtotalCents = lines.reduce(
      (sum, line) => sum + line.unitPriceCents * line.quantity,
      0,
    );

    const coupon = this.validateCoupon(
      lines,
      subtotalCents,
      currency,
      couponRecord,
      couponCodeInput,
    );

    const discountCents = coupon.valid
      ? (coupon.discount?.amountCents ?? 0)
      : 0;
    const taxableCents = Math.max(0, subtotalCents - discountCents);
    const shippingCents =
      subtotalCents >= storeConfig.freeShippingThresholdCents
        ? 0
        : storeConfig.flatShippingCents;
    const taxCents = Math.round(
      (taxableCents * storeConfig.taxRateBps) / 10_000,
    );
    const totalCents = taxableCents + shippingCents + taxCents;

    return {
      lines: lineResponses,
      subtotalCents,
      discountCents,
      shippingCents,
      taxCents,
      totalCents,
      currency,
      coupon,
      appliedCouponId:
        coupon.valid && couponRecord !== null ? couponRecord.id : null,
      appliedCouponCode:
        coupon.valid && couponRecord !== null ? couponRecord.code : null,
    };
  }

  validateCoupon(
    lines: PricedLineContext[],
    subtotalCents: number,
    currency: string,
    coupon: CouponWithExclusions | null,
    couponCodeInput: string | undefined,
  ): CouponValidationDto {
    if (couponCodeInput === undefined || couponCodeInput.trim().length === 0) {
      return { valid: false };
    }

    const normalizedCode = couponCodeInput.trim().toUpperCase();
    if (coupon === null) {
      return {
        valid: false,
        code: normalizedCode,
        rejectionReason: CouponRejectionReason.INVALID,
      };
    }

    if (!coupon.isActive) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.INVALID,
      };
    }

    const now = new Date();
    if (coupon.startsAt !== null && coupon.startsAt > now) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.INVALID,
      };
    }
    if (coupon.expiresAt !== null && coupon.expiresAt < now) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.EXPIRED,
      };
    }
    if (
      coupon.maxRedemptions !== null &&
      coupon.redemptionCount >= coupon.maxRedemptions
    ) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.INVALID,
      };
    }
    if (subtotalCents < coupon.minSubtotalCents) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.MINIMUM_NOT_MET,
      };
    }

    if (this.cartHasExcludedItems(lines, coupon.exclusions)) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.EXCLUDED_ITEMS,
      };
    }

    const discountCents = this.computeDiscountCents(
      coupon,
      lines,
      subtotalCents,
    );
    if (discountCents <= 0) {
      return {
        valid: false,
        code: coupon.code,
        rejectionReason: CouponRejectionReason.EXCLUDED_ITEMS,
      };
    }

    return {
      valid: true,
      code: coupon.code,
      discount: { amountCents: discountCents, currency },
    };
  }

  private cartHasExcludedItems(
    lines: PricedLineContext[],
    exclusions: CouponExclusion[],
  ): boolean {
    if (exclusions.length === 0) {
      return false;
    }
    for (const line of lines) {
      for (const exclusion of exclusions) {
        if (
          exclusion.kind === CouponExclusionKind.PRODUCT &&
          exclusion.productId === line.productId
        ) {
          return true;
        }
        if (
          exclusion.kind === CouponExclusionKind.CATEGORY &&
          exclusion.categoryId === line.categoryId
        ) {
          return true;
        }
      }
    }
    return false;
  }

  private computeDiscountCents(
    coupon: Coupon,
    lines: PricedLineContext[],
    subtotalCents: number,
  ): number {
    if (coupon.type === CouponType.FIXED_AMOUNT) {
      const amount = coupon.amountOffCents ?? 0;
      return Math.min(amount, subtotalCents);
    }
    const percent = coupon.percentOff ?? 0;
    return Math.floor((subtotalCents * percent) / 100);
  }
}
