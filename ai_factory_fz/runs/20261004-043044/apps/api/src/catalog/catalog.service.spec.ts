import { BadRequestException, NotFoundException } from '@nestjs/common';
import { Decimal } from '@prisma/client/runtime/library';
import { M1_CATALOG_PARITY } from './catalog-seed.constants';
import { CatalogAnalyticsService } from './catalog-analytics.service';
import { CatalogService } from './catalog.service';
import { PrismaService } from '../prisma/prisma.service';

describe('CatalogService', () => {
  const rootCategory = {
    id: 'c1111111-1111-4111-8111-111111111101',
    name: 'Ceiling Lights',
    slug: 'ceiling-lights',
    parentId: null,
    imageUrl: 'assets/images/products/placeholder.png',
    description: null,
    sortOrder: 1,
    isActive: true,
  };

  const childCategory = {
    id: 'c1111111-1111-4111-8111-111111111108',
    name: 'Pendant Lights',
    slug: 'pendant-lights',
    parentId: rootCategory.id,
    imageUrl: 'assets/images/products/placeholder.png',
    description: null,
    sortOrder: 2,
    isActive: true,
  };

  const featuredProduct = {
    id: 'p1111111-1111-4111-8111-111111111101',
    name: 'Modern LED Ceiling Light',
    slug: 'modern-led-ceiling-light',
    primaryImageUrl: 'assets/images/products/cl-1001.png',
    averageRating: new Decimal('4.50'),
    reviewCount: 12,
    popularityRank: 1,
    isActive: true,
    isFeatured: true,
    brand: { name: 'Luminex' },
    category: {
      id: rootCategory.id,
      name: rootCategory.name,
      slug: rootCategory.slug,
      parentId: null,
      imageUrl: rootCategory.imageUrl,
    },
    variants: [
      {
        isActive: true,
        isDefault: true,
        priceCents: 4999,
        currency: 'GBP',
        compareAtCents: null,
        stockQuantity: 10,
        reservedQuantity: 0,
        sku: 'CL-1001-WH',
      },
    ],
  };

  let categoryFindMany: jest.Mock;
  let categoryFindFirst: jest.Mock;
  let homeBannerFindMany: jest.Mock;
  let productFindMany: jest.Mock;
  let productFindFirst: jest.Mock;
  let reviewCount: jest.Mock;
  let reviewFindMany: jest.Mock;
  let recordProductView: jest.Mock;
  let service: CatalogService;

  const homeBanner = {
    id: 'h1111111-1111-4111-8111-111111111101',
    title: 'Winter Lighting Sale',
    subtitle: 'Save on ceiling fixtures',
    imageUrl: 'assets/images/banners/winter-sale.png',
    ctaLabel: 'Shop now',
    categorySlug: 'ceiling-lights',
    sortOrder: 1,
    isActive: true,
  };

  const listProduct = {
    ...featuredProduct,
    description: 'A modern ceiling light',
    unitsSold90Days: 42,
    specs: { wattageW: 24, finish: 'Matte White' },
    createdAt: new Date('2025-06-01T00:00:00.000Z'),
  };

  beforeEach(() => {
    categoryFindMany = jest.fn();
    categoryFindFirst = jest.fn();
    homeBannerFindMany = jest.fn();
    productFindMany = jest.fn();
    productFindFirst = jest.fn();
    reviewCount = jest.fn();
    reviewFindMany = jest.fn();

    const prisma = {
      category: {
        findMany: categoryFindMany,
        findFirst: categoryFindFirst,
      },
      homeBanner: {
        findMany: homeBannerFindMany,
      },
      product: {
        findMany: productFindMany,
        findFirst: productFindFirst,
      },
      review: {
        count: reviewCount,
        findMany: reviewFindMany,
      },
    };

    recordProductView = jest.fn();
    const catalogAnalytics = {
      recordProductView,
    };

    service = new CatalogService(
      prisma as unknown as PrismaService,
      catalogAnalytics as unknown as CatalogAnalyticsService,
    );
  });

  describe('getHome', () => {
    it('returns categories, banners, featured products, and new arrivals', async () => {
      categoryFindMany.mockResolvedValue([rootCategory]);
      homeBannerFindMany.mockResolvedValue([homeBanner]);
      productFindMany
        .mockResolvedValueOnce([featuredProduct])
        .mockResolvedValueOnce([featuredProduct]);

      const result = await service.getHome();

      expect(result.categories).toHaveLength(1);
      expect(result.categories[0].slug).toBe('ceiling-lights');
      expect(result.banners).toHaveLength(1);
      expect(result.banners[0].title).toBe('Winter Lighting Sale');
      expect(result.featuredProducts).toHaveLength(1);
      expect(result.featuredProducts[0].price).toEqual({
        amountCents: 4999,
        currency: 'GBP',
      });
      expect(result.newArrivals).toHaveLength(1);

      expect(categoryFindMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { isActive: true, parentId: null },
        }),
      );
      expect(homeBannerFindMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { isActive: true },
        }),
      );
      expect(productFindMany).toHaveBeenNthCalledWith(
        1,
        expect.objectContaining({
          where: { isActive: true, isFeatured: true },
        }),
      );
      expect(productFindMany).toHaveBeenNthCalledWith(
        2,
        expect.objectContaining({
          where: { isActive: true },
          orderBy: { createdAt: 'desc' },
        }),
      );
    });
  });

  describe('listCategories', () => {
    it('returns only root categories when depth is 1', async () => {
      categoryFindMany.mockResolvedValue([rootCategory]);

      const result = await service.listCategories(1);

      expect(result.items).toHaveLength(1);
      expect(categoryFindMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { isActive: true, parentId: null },
        }),
      );
    });

    it('returns all active categories when depth is 2', async () => {
      categoryFindMany.mockResolvedValue([rootCategory, childCategory]);

      const result = await service.listCategories(2);

      expect(result.items).toHaveLength(2);
      expect(result.items[1].parentId).toBe(rootCategory.id);
      expect(categoryFindMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { isActive: true },
        }),
      );
    });
  });

  describe('getCategoryBySlug', () => {
    it('returns category detail with children', async () => {
      categoryFindFirst.mockResolvedValue({
        ...rootCategory,
        description: 'Ceiling lighting range',
      });
      categoryFindMany.mockResolvedValue([childCategory]);

      const result = await service.getCategoryBySlug('ceiling-lights');

      expect(result.slug).toBe('ceiling-lights');
      expect(result.description).toBe('Ceiling lighting range');
      expect(result.children).toHaveLength(1);
      expect(result.children![0].slug).toBe('pendant-lights');
    });

    it('throws NotFoundException when slug is unknown', async () => {
      categoryFindFirst.mockResolvedValue(null);

      await expect(service.getCategoryBySlug('missing')).rejects.toBeInstanceOf(
        NotFoundException,
      );
    });
  });

  describe('listProducts', () => {
    it('returns paginated summaries matching search query', async () => {
      productFindMany.mockResolvedValue([listProduct]);

      const result = await service.listProducts({
        page: 1,
        pageSize: 20,
        q: 'Modern LED',
        sort: 'popularity' as never,
        inStockOnly: false,
      });

      expect(result.total).toBe(1);
      expect(result.items[0].name).toBe('Modern LED Ceiling Light');
    });

    it('throws BadRequestException when price range is invalid', async () => {
      await expect(
        service.listProducts({
          page: 1,
          pageSize: 20,
          minPriceCents: 5000,
          maxPriceCents: 1000,
          sort: 'popularity' as never,
          inStockOnly: false,
        }),
      ).rejects.toBeInstanceOf(BadRequestException);
    });
  });

  describe('getProductById', () => {
    it('returns product detail with variants and specs', async () => {
      productFindFirst.mockResolvedValue({
        ...listProduct,
        images: [{ url: 'assets/gallery.png', sortOrder: 0, altText: 'Front' }],
        variants: [
          {
            id: 'v1',
            sku: 'CL-1001-WH',
            label: 'White',
            priceCents: 4999,
            currency: 'GBP',
            compareAtCents: null,
            stockQuantity: 10,
            reservedQuantity: 0,
            isDefault: true,
            isActive: true,
          },
        ],
      });

      const detail = await service.getProductById(listProduct.id);

      expect(detail.id).toBe(listProduct.id);
      expect(detail.variants).toHaveLength(1);
      expect(detail.specs.wattageW).toBe(24);
      expect(detail.unitsSold90Days).toBe(42);
      expect(recordProductView).toHaveBeenCalledWith(listProduct.id, undefined);
    });

    it('records analytics context when provided', async () => {
      productFindFirst.mockResolvedValue({
        ...listProduct,
        images: [],
        variants: [
          {
            id: 'v1',
            sku: 'CL-1001-WH',
            label: 'White',
            priceCents: 4999,
            currency: 'GBP',
            compareAtCents: null,
            stockQuantity: 10,
            reservedQuantity: 0,
            isDefault: true,
            isActive: true,
          },
        ],
      });

      await service.getProductById(listProduct.id, {
        userId: 'u1',
        sessionId: 'guest-1',
      });

      expect(recordProductView).toHaveBeenCalledWith(listProduct.id, {
        userId: 'u1',
        sessionId: 'guest-1',
      });
    });

    it('throws NotFoundException when product is missing', async () => {
      productFindFirst.mockResolvedValue(null);
      await expect(service.getProductById(listProduct.id)).rejects.toBeInstanceOf(
        NotFoundException,
      );
      expect(recordProductView).not.toHaveBeenCalled();
    });
  });

  describe('listProductReviews', () => {
    it('returns paginated reviews with aggregate rating', async () => {
      productFindFirst.mockResolvedValue({
        id: listProduct.id,
        averageRating: new Decimal('4.50'),
        reviewCount: 1,
      });
      reviewCount.mockResolvedValue(1);
      reviewFindMany.mockResolvedValue([
        {
          id: 'r1',
          rating: 5,
          title: 'Great light',
          body: 'Very bright',
          authorDisplayName: 'Verified Buyer',
          createdAt: new Date('2025-07-01T12:00:00.000Z'),
        },
      ]);

      const result = await service.listProductReviews(listProduct.id, {
        page: 1,
        pageSize: 10,
      });

      expect(result.total).toBe(1);
      expect(result.rating.reviewCount).toBe(1);
      expect(result.items[0].authorDisplayName).toBe('Verified Buyer');
    });
  });

  describe('getCatalogFacets', () => {
    it('aggregates brand counts and price bounds from scoped products', async () => {
      productFindMany.mockResolvedValue([listProduct]);

      const facets = await service.getCatalogFacets({});

      expect(facets.brands).toEqual([{ name: 'Luminex', productCount: 1 }]);
      expect(facets.price).toEqual({ minPriceCents: 4999, maxPriceCents: 4999 });
    });
  });

  it('parity constant documents four featured products for home carousel', () => {
    expect(M1_CATALOG_PARITY.featuredProductCount).toBe(4);
  });
});
