export type CheckoutCouponLine = {
  productId: string;
  variantId: string;
  lineSubtotalCents: number;
  categoryId: string;
  isOnSale: boolean;
};

export type LoadedCoupon = {
  id: string;
  code: string;
  description: string | null;
  percentOff: number | null;
  amountOffCents: number | null;
  currency: string;
  minSubtotalCents: number | null;
  expiresAt: Date | null;
  singleUsePerEmail: boolean;
  excludeSaleItems: boolean;
  isActive: boolean;
  categoryIds: string[];
  productIds: string[];
};

export type AppliedCouponPreview = {
  couponApplied: true;
  couponCode: string;
  discountCents: number;
  couponMessage?: string;
};
