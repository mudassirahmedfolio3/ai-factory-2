import {
  COUPON_MINIMUM_NOT_MET_MESSAGE,
  COUPON_NOT_ELIGIBLE_MESSAGE,
  COUPON_STACKING_MESSAGE,
} from './checkout.constants';
import { AppliedCouponPreview, CheckoutCouponLine, LoadedCoupon } from './checkout-coupon.types';

export class CouponValidationError extends Error {
  constructor(readonly clientMessage: string) {
    super(clientMessage);
    this.name = 'CouponValidationError';
  }
}

export function parseCouponCodeInput(raw: string): string[] {
  const trimmed = raw.trim();
  if (!trimmed) {
    return [];
  }

  const parts = trimmed
    .split(/[,;+\s]+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 0);

  if (parts.length > 1) {
    throw new CouponValidationError(COUPON_STACKING_MESSAGE);
  }

  return [parts[0]!.toUpperCase()];
}

export function isCouponExpired(expiresAt: Date | null, now: Date): boolean {
  return expiresAt != null && expiresAt.getTime() <= now.getTime();
}

function lineEligibleForCoupon(line: CheckoutCouponLine, coupon: LoadedCoupon): boolean {
  const hasCategoryScope = coupon.categoryIds.length > 0;
  const hasProductScope = coupon.productIds.length > 0;

  if (!hasCategoryScope && !hasProductScope) {
    return true;
  }

  if (hasProductScope && coupon.productIds.includes(line.productId)) {
    return true;
  }

  if (hasCategoryScope && coupon.categoryIds.includes(line.categoryId)) {
    return true;
  }

  return false;
}

function eligibleLines(lines: CheckoutCouponLine[], coupon: LoadedCoupon): CheckoutCouponLine[] {
  return lines.filter((line) => {
    if (coupon.excludeSaleItems && line.isOnSale) {
      return false;
    }
    return lineEligibleForCoupon(line, coupon);
  });
}

export function computeCouponDiscountCents(
  cartSubtotalCents: number,
  lines: CheckoutCouponLine[],
  coupon: LoadedCoupon,
): AppliedCouponPreview {
  if (coupon.minSubtotalCents != null && cartSubtotalCents < coupon.minSubtotalCents) {
    throw new CouponValidationError(COUPON_MINIMUM_NOT_MET_MESSAGE);
  }

  const qualifying = eligibleLines(lines, coupon);
  const eligibleSubtotalCents = qualifying.reduce((sum, line) => sum + line.lineSubtotalCents, 0);

  if (eligibleSubtotalCents <= 0) {
    throw new CouponValidationError(COUPON_NOT_ELIGIBLE_MESSAGE);
  }

  let discountCents = 0;
  if (coupon.percentOff != null) {
    discountCents = Math.floor((eligibleSubtotalCents * coupon.percentOff) / 100);
  } else if (coupon.amountOffCents != null) {
    discountCents = Math.min(coupon.amountOffCents, eligibleSubtotalCents);
  }

  if (discountCents <= 0) {
    throw new CouponValidationError(COUPON_NOT_ELIGIBLE_MESSAGE);
  }

  return {
    couponApplied: true,
    couponCode: coupon.code,
    discountCents,
    couponMessage: coupon.description ?? undefined,
  };
}
