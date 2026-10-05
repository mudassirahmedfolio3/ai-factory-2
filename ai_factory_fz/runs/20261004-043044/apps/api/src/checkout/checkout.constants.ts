export const INVALID_UK_ADDRESS_MESSAGE =
  'Shipping is limited to standard UK mainland addresses';

export const SHIPPING_LABEL_STANDARD = 'Standard UK domestic delivery only';
export const SHIPPING_LABEL_FREE = 'Free standard UK domestic delivery';

export const DEFAULT_UK_SHIPPING_FLAT_RATE_CENTS = 495;
export const DEFAULT_UK_FREE_DELIVERY_THRESHOLD_CENTS = 7500;

export const COUPON_STACKING_MESSAGE = 'Only one coupon code is allowed per order';
export const COUPON_NOT_FOUND_MESSAGE = 'Coupon code is not valid';
export const COUPON_INACTIVE_MESSAGE = 'This coupon is not active';
export const COUPON_EXPIRED_MESSAGE = 'This coupon has expired';
export const COUPON_MINIMUM_NOT_MET_MESSAGE =
  'Your order does not meet the minimum value for this coupon';
export const COUPON_NOT_ELIGIBLE_MESSAGE =
  'This coupon does not apply to the items in your cart';
export const COUPON_CURRENCY_MISMATCH_MESSAGE = 'This coupon cannot be used with this cart';
export const COUPON_ALREADY_USED_MESSAGE = 'This coupon has already been used on your account';

export const IDEMPOTENCY_KEY_REQUIRED_MESSAGE = 'Idempotency-Key header is required';
export const IDEMPOTENCY_KEY_TOO_LONG_MESSAGE = 'Idempotency-Key must be at most 64 characters';
export const INVALID_CHECKOUT_MESSAGE = 'Checkout could not be completed';

export const DEFAULT_MOCK_PAYMENT_SESSION_EXPIRES_SECONDS = 900;
export const DEFAULT_STOCK_RESERVATION_EXPIRES_SECONDS = 900;
