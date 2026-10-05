import {
  calculateCheckoutTotalCents,
  calculateUkShippingQuote,
} from './checkout-shipping';
import {
  SHIPPING_LABEL_FREE,
  SHIPPING_LABEL_STANDARD,
} from './checkout.constants';

describe('checkout-shipping', () => {
  const flatRate = 495;
  const threshold = 7500;

  it('applies flat rate below threshold', () => {
    const quote = calculateUkShippingQuote(4999, flatRate, threshold);
    expect(quote.shippingCents).toBe(495);
    expect(quote.shippingLabel).toBe(SHIPPING_LABEL_STANDARD);
    expect(quote.freeDeliveryThresholdCents).toBe(7500);
  });

  it('waives shipping at or above threshold', () => {
    const quote = calculateUkShippingQuote(7500, flatRate, threshold);
    expect(quote.shippingCents).toBe(0);
    expect(quote.shippingLabel).toBe(SHIPPING_LABEL_FREE);
  });

  it('computes checkout total in pence', () => {
    expect(calculateCheckoutTotalCents(5000, 495, 0)).toBe(5495);
    expect(calculateCheckoutTotalCents(8000, 0, 500)).toBe(7500);
  });
});
