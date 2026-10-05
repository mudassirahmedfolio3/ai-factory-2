import { describe, expect, it } from 'vitest';
import { toCartItemResponse, toCartResponse } from './cart.mapper.js';

describe('cart.mapper', () => {
  it('maps cart lines with line totals and subtotal', () => {
    const item = {
      id: 'line-1',
      cartId: 'cart-1',
      variantId: 'var-1',
      quantity: 2,
      unitPriceCents: 1500,
      currency: 'USD',
      productName: 'Soap',
      variantName: 'Default',
      createdAt: new Date(),
      updatedAt: new Date(),
      variant: { productId: 'prod-1' },
    };

    expect(toCartItemResponse(item)).toEqual({
      id: 'line-1',
      variantId: 'var-1',
      productId: 'prod-1',
      productName: 'Soap',
      variantName: 'Default',
      quantity: 2,
      unitPrice: { amountCents: 1500, currency: 'USD' },
      lineTotal: { amountCents: 3000, currency: 'USD' },
    });

    expect(toCartResponse([item])).toEqual({
      items: [expect.objectContaining({ id: 'line-1' })],
      subtotal: { amountCents: 3000, currency: 'USD' },
    });
  });
});
