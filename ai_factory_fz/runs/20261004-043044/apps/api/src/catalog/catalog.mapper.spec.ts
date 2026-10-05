import { Decimal } from '@prisma/client/runtime/library';
import {
  productInStock,
  toCategorySummary,
  toHomeBannerDto,
  toLightingSpecs,
  toProductDetail,
  toProductSummary,
} from './catalog.mapper';

describe('catalog.mapper', () => {
  describe('toHomeBannerDto', () => {
    it('maps optional subtitle and category slug', () => {
      expect(
        toHomeBannerDto({
          id: 'h1',
          title: 'Sale',
          subtitle: 'Limited time',
          imageUrl: 'assets/banner.png',
          ctaLabel: 'Shop',
          categorySlug: 'ceiling-lights',
        } as never),
      ).toEqual({
        id: 'h1',
        title: 'Sale',
        subtitle: 'Limited time',
        imageUrl: 'assets/banner.png',
        ctaLabel: 'Shop',
        categorySlug: 'ceiling-lights',
      });
    });
  });

  describe('toCategorySummary', () => {
    it('omits parentId for top-level categories', () => {
      expect(
        toCategorySummary({
          id: 'c1',
          name: 'Ceiling',
          slug: 'ceiling-lights',
          parentId: null,
          imageUrl: 'assets/x.png',
        }),
      ).toEqual({
        id: 'c1',
        name: 'Ceiling',
        slug: 'ceiling-lights',
        imageUrl: 'assets/x.png',
      });
    });
  });

  describe('productInStock', () => {
    it('is true when any active variant has available quantity', () => {
      expect(
        productInStock([
          {
            isActive: true,
            stockQuantity: 0,
            reservedQuantity: 0,
          } as never,
          {
            isActive: true,
            stockQuantity: 5,
            reservedQuantity: 2,
          } as never,
        ]),
      ).toBe(true);
    });

    it('is false when no active variant has stock', () => {
      expect(
        productInStock([
          {
            isActive: false,
            stockQuantity: 10,
            reservedQuantity: 0,
          } as never,
          {
            isActive: true,
            stockQuantity: 1,
            reservedQuantity: 1,
          } as never,
        ]),
      ).toBe(false);
    });
  });

  describe('toProductSummary', () => {
    it('uses default variant price in GBP minor units', () => {
      const summary = toProductSummary({
        id: 'p1',
        name: 'Test Light',
        slug: 'test-light',
        primaryImageUrl: 'assets/p.png',
        averageRating: new Decimal('4.50'),
        reviewCount: 3,
        popularityRank: 2,
        brand: { name: 'Luminex' },
        category: {
          id: 'c1',
          name: 'Ceiling',
          slug: 'ceiling-lights',
          parentId: null,
          imageUrl: null,
        },
        variants: [
          {
            isActive: true,
            isDefault: false,
            priceCents: 9999,
            currency: 'GBP',
            compareAtCents: null,
            stockQuantity: 0,
            reservedQuantity: 0,
          },
          {
            isActive: true,
            isDefault: true,
            priceCents: 4999,
            currency: 'GBP',
            compareAtCents: 5999,
            stockQuantity: 4,
            reservedQuantity: 0,
          },
        ],
      } as never);

      expect(summary.price).toEqual({ amountCents: 4999, currency: 'GBP' });
      expect(summary.compareAtPrice).toEqual({ amountCents: 5999, currency: 'GBP' });
      expect(summary.inStock).toBe(true);
      expect(summary.rating).toEqual({ averageRating: 4.5, reviewCount: 3 });
      expect(summary.popularityRank).toBe(2);
    });
  });

  describe('toLightingSpecs', () => {
    it('omits null specification fields', () => {
      expect(
        toLightingSpecs({
          wattageW: 24,
          lumens: null,
          colorTemperatureK: 3000,
          lightType: null,
          voltage: null,
          dimmable: true,
          material: null,
          finish: 'Matte Black',
          dimensionsMm: null,
          ipRating: 'IP44',
          bulbIncluded: null,
          installationType: null,
        } as never),
      ).toEqual({
        wattageW: 24,
        colorTemperatureK: 3000,
        dimmable: true,
        finish: 'Matte Black',
        ipRating: 'IP44',
      });
    });
  });

  describe('toProductDetail', () => {
    it('maps variants with available quantity and sorted images', () => {
      const detail = toProductDetail({
        id: 'p1',
        name: 'Test Light',
        slug: 'test-light',
        description: 'Full description',
        primaryImageUrl: 'assets/p.png',
        averageRating: new Decimal('4.50'),
        reviewCount: 3,
        popularityRank: 2,
        unitsSold90Days: 9,
        brand: { name: 'Luminex' },
        category: {
          id: 'c1',
          name: 'Ceiling',
          slug: 'ceiling-lights',
          parentId: null,
          imageUrl: null,
        },
        variants: [
          {
            id: 'v1',
            sku: 'CL-1001-WH',
            label: 'White',
            priceCents: 4999,
            currency: 'GBP',
            compareAtCents: null,
            stockQuantity: 4,
            reservedQuantity: 1,
            isDefault: true,
            isActive: true,
          },
        ],
        specs: { wattageW: 24 } as never,
        images: [
          { url: 'assets/b.png', sortOrder: 1, altText: null },
          { url: 'assets/a.png', sortOrder: 0, altText: 'Front' },
        ],
      } as never);

      expect(detail.variants[0].availableQuantity).toBe(3);
      expect(detail.images[0].url).toBe('assets/a.png');
      expect(detail.unitsSold90Days).toBe(9);
    });
  });
});
