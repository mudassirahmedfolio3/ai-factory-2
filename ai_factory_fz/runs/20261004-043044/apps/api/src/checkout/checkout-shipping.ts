import {
  SHIPPING_LABEL_FREE,
  SHIPPING_LABEL_STANDARD,
} from './checkout.constants';

export type ShippingQuote = {
  shippingCents: number;
  shippingLabel: string;
  freeDeliveryThresholdCents: number;
};

export function calculateUkShippingQuote(
  subtotalCents: number,
  flatRateCents: number,
  freeDeliveryThresholdCents: number,
): ShippingQuote {
  const qualifiesForFreeDelivery = subtotalCents >= freeDeliveryThresholdCents;
  const shippingCents = qualifiesForFreeDelivery ? 0 : flatRateCents;
  const shippingLabel = qualifiesForFreeDelivery
    ? SHIPPING_LABEL_FREE
    : SHIPPING_LABEL_STANDARD;

  return {
    shippingCents,
    shippingLabel,
    freeDeliveryThresholdCents,
  };
}

export function calculateCheckoutTotalCents(
  subtotalCents: number,
  shippingCents: number,
  discountCents: number,
): number {
  return Math.max(0, subtotalCents - discountCents + shippingCents);
}
