import { Decimal } from '@prisma/client/runtime/library';
import {
  productMatchesListQuery,
  sortProductsForListing,
} from './catalog-product.filters';
import { ProductSort } from './dto/list-products-query.dto';

const baseProduct = {
  id: 'p1',
  name: 'Modern LED Ceiling Light',
  slug: 'modern-led-ceiling-light',
  description: 'Bright ceiling fixture for kitchens',
  primaryImageUrl: 'assets/p.png',
  averageRating: new Decimal('4.5'),
  reviewCount: 2,
  popularityRank: 5,
  unitsSold90Days: 10,
  createdAt: new Date('2025-01-01T00:00:00.000Z'),
  brand: { name: 'Luminex' },
  category: {
    id: 'c1',
    name: 'Ceiling',
    slug: 'ceiling-lights',
    parentId: null,
    imageUrl: null,
  },
  specs: {
    wattageW: 24,
    finish: 'Matte White',
  },
  variants: [
    {
      isActive: true,
      isDefault: true,
      sku: 'CL-1001-WH',
      priceCents: 4999,
      currency: 'GBP',
      compareAtCents: null,
      stockQuantity: 3,
      reservedQuantity: 0,
      finish: 'Matte White',
      wattageW: 24,
    },
  ],
} as never;

describe('catalog-product.filters', () => {
  describe('productMatchesListQuery', () => {
    it('matches search by product name and SKU', () => {
      expect(
        productMatchesListQuery(
          baseProduct,
          { q: 'Modern LED', page: 1, pageSize: 20, sort: ProductSort.Popularity, inStockOnly: false },
          undefined,
        ),
      ).toBe(true);
      expect(
        productMatchesListQuery(
          baseProduct,
          { q: 'CL-1001', page: 1, pageSize: 20, sort: ProductSort.Popularity, inStockOnly: false },
          undefined,
        ),
      ).toBe(true);
      expect(
        productMatchesListQuery(
          baseProduct,
          { q: 'no-match-term', page: 1, pageSize: 20, sort: ProductSort.Popularity, inStockOnly: false },
          undefined,
        ),
      ).toBe(false);
    });

    it('filters by brand and inStockOnly', () => {
      expect(
        productMatchesListQuery(
          baseProduct,
          {
            brand: ['Luminex'],
            page: 1,
            pageSize: 20,
            sort: ProductSort.Popularity,
            inStockOnly: false,
          },
          undefined,
        ),
      ).toBe(true);
      expect(
        productMatchesListQuery(
          baseProduct,
          {
            brand: ['OtherBrand'],
            page: 1,
            pageSize: 20,
            sort: ProductSort.Popularity,
            inStockOnly: false,
          },
          undefined,
        ),
      ).toBe(false);
      expect(
        productMatchesListQuery(
          baseProduct,
          {
            page: 1,
            pageSize: 20,
            sort: ProductSort.Popularity,
            inStockOnly: true,
          },
          undefined,
        ),
      ).toBe(true);
    });
  });

  describe('sortProductsForListing', () => {
    const highRank = {
      ...baseProduct,
      id: 'p-high',
      popularityRank: 1,
      unitsSold90Days: 5,
    };
    const lowRank = {
      ...baseProduct,
      id: 'p-low',
      popularityRank: 10,
      unitsSold90Days: 50,
    };

    it('orders popularity by rank then units sold', () => {
      const sorted = sortProductsForListing(
        [lowRank, highRank],
        ProductSort.Popularity,
      );
      expect(sorted.map((p) => p.id)).toEqual(['p-high', 'p-low']);
    });

    it('orders price ascending by listing price', () => {
      const expensive = {
        ...baseProduct,
        id: 'p-exp',
        variants: [{ ...baseProduct.variants[0], priceCents: 9999 }],
      };
      const cheap = {
        ...baseProduct,
        id: 'p-cheap',
        variants: [{ ...baseProduct.variants[0], priceCents: 1999 }],
      };
      const sorted = sortProductsForListing(
        [expensive, cheap],
        ProductSort.PriceAsc,
      );
      expect(sorted.map((p) => p.id)).toEqual(['p-cheap', 'p-exp']);
    });
  });
});
