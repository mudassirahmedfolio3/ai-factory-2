import { describe, expect, it } from 'vitest';
import {
  productAvailability,
  stockAvailable,
  toProductSummary,
} from './catalog.mapper.js';
import { AvailabilityStatus } from './dto/catalog.responses.js';

describe('catalog.mapper', () => {
  it('computes stockAvailable from quantity minus reserved', () => {
    expect(stockAvailable({ stockQuantity: 10, reservedQuantity: 3 })).toBe(7);
    expect(stockAvailable({ stockQuantity: 2, reservedQuantity: 5 })).toBe(0);
  });

  it('maps product availability from the best variant stock level', () => {
    expect(
      productAvailability(
        [
          { stockQuantity: 0, reservedQuantity: 0 },
          { stockQuantity: 3, reservedQuantity: 0 },
        ],
        5,
      ),
    ).toBe(AvailabilityStatus.LOW_STOCK);

    expect(
      productAvailability([{ stockQuantity: 20, reservedQuantity: 0 }], 5),
    ).toBe(AvailabilityStatus.IN_STOCK);

    expect(
      productAvailability([{ stockQuantity: 0, reservedQuantity: 0 }], 5),
    ).toBe(AvailabilityStatus.OUT_OF_STOCK);
  });

  it('maps ProductSummary with nested category and USD cents', () => {
    const summary = toProductSummary(
      {
        id: 'prod-1',
        name: 'Citrus Hand Soap',
        brand: 'PureNest',
        description: 'desc',
        primaryImageUrl: 'https://example.com/a.jpg',
        createdAt: new Date(),
        category: {
          id: 'cat-1',
          slug: 'personal-care',
          name: 'Personal Care',
        },
        variants: [
          {
            id: 'var-1',
            sku: 'SKU-1',
            name: '300 ml',
            priceCents: 799,
            currency: 'USD',
            stockQuantity: 16,
            reservedQuantity: 0,
            imageUrl: null,
            isDefault: true,
            isActive: true,
          },
        ],
      },
      5,
    );

    expect(summary).toMatchObject({
      id: 'prod-1',
      brand: 'PureNest',
      category: { slug: 'personal-care', name: 'Personal Care' },
      price: { amountCents: 799, currency: 'USD' },
      availability: AvailabilityStatus.IN_STOCK,
    });
  });
});
