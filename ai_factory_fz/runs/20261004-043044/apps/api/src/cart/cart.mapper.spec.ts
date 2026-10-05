import { toCartLineItem, toCartResponse } from './cart.mapper';

describe('cart.mapper', () => {
  const variant = {
    id: 'b1111111-1111-4111-8111-111111111111',
    productId: 'p1111111-1111-4111-8111-111111111111',
    sku: 'CL-1001-WH',
    label: 'White',
    priceCents: 4999,
    compareAtCents: null,
    currency: 'GBP',
    stockQuantity: 10,
    reservedQuantity: 0,
    finish: null,
    wattageW: null,
    colorTemperatureK: null,
    imageUrl: 'assets/variant.png',
    isDefault: true,
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    product: {
      id: 'p1111111-1111-4111-8111-111111111111',
      name: 'Modern LED Ceiling Light',
      primaryImageUrl: 'assets/product.png',
      isActive: true,
    },
  };

  it('maps line subtotal from integer pence snapshot', () => {
    const line = {
      id: 'd1111111-1111-4111-8111-111111111111',
      cartId: 'c1111111-1111-4111-8111-111111111111',
      variantId: variant.id,
      quantity: 2,
      unitPriceCents: 4999,
      currency: 'GBP',
      productName: 'Modern LED Ceiling Light',
      variantLabel: 'White',
      sku: 'CL-1001-WH',
      createdAt: new Date(),
      updatedAt: new Date(),
      variant,
    };

    const dto = toCartLineItem(line);
    expect(dto.lineSubtotalCents).toBe(9998);
    expect(dto.unitPrice.amountCents).toBe(4999);
    expect(dto.imageUrl).toBe('assets/variant.png');
  });

  it('aggregates cart totals and item count', () => {
    const line = {
      id: 'd1111111-1111-4111-8111-111111111111',
      cartId: 'c1111111-1111-4111-8111-111111111111',
      variantId: variant.id,
      quantity: 3,
      unitPriceCents: 1000,
      currency: 'GBP',
      productName: 'Lamp',
      variantLabel: 'Default',
      sku: 'L-1',
      createdAt: new Date(),
      updatedAt: new Date(),
      variant,
    };

    const response = toCartResponse('cart-id', [line], { guestCartId: 'cart-id' });
    expect(response.subtotalCents).toBe(3000);
    expect(response.itemCount).toBe(3);
    expect(response.guestCartId).toBe('cart-id');
    expect(response.currency).toBe('GBP');
  });
});
