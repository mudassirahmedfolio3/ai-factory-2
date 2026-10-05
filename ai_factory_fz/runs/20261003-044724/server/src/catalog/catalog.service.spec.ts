import { BadRequestException, NotFoundException } from '@nestjs/common';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogService } from './catalog.service.js';
import { AvailabilityStatus } from './dto/catalog.responses.js';
import {
  AvailabilityFilter,
  ProductSort,
} from './dto/list-products.query.js';

type FindManyResult = {
  id: string;
  name: string;
  brand: string;
  description: string;
  primaryImageUrl: string;
  createdAt: Date;
  category: { id: string; slug: string; name: string };
  variants: Array<{
    id: string;
    sku: string;
    name: string;
    priceCents: number;
    currency: string;
    stockQuantity: number;
    reservedQuantity: number;
    imageUrl: string | null;
    isDefault: boolean;
    isActive: boolean;
  }>;
};

describe('CatalogService', () => {
  const prisma = {
    category: { findMany: vi.fn() },
    product: { findMany: vi.fn(), count: vi.fn(), findFirst: vi.fn() },
    storeConfig: { findUnique: vi.fn() },
    $transaction: vi.fn(),
  };
  let service: CatalogService;

  beforeEach(() => {
    vi.resetAllMocks();
    prisma.$transaction.mockImplementation(
      (ops: Promise<unknown>[]) => Promise.all(ops),
    );
    prisma.storeConfig.findUnique.mockResolvedValue({ lowStockThreshold: 5 });
    service = new CatalogService(prisma as never);
  });

  function mockProduct(overrides: Partial<FindManyResult> = {}): FindManyResult {
    return {
      id: 'prod-1',
      name: 'Citrus Hand Soap',
      brand: 'PureNest',
      description: 'desc',
      primaryImageUrl: 'https://example.com/a.jpg',
      createdAt: new Date('2026-01-02T00:00:00.000Z'),
      category: {
        id: 'cat-1',
        slug: 'personal-care',
        name: 'Personal Care',
      },
      variants: [
        {
          id: 'var-1',
          sku: 'SHO-SOAP-300',
          name: '300 ml',
          priceCents: 799,
          currency: 'USD',
          stockQuantity: 16,
          reservedQuantity: 0,
          imageUrl: null,
          isDefault: true,
          isActive: true,
        },
        {
          id: 'var-2',
          sku: 'SHO-SOAP-500',
          name: '500 ml',
          priceCents: 1099,
          currency: 'USD',
          stockQuantity: 8,
          reservedQuantity: 0,
          imageUrl: null,
          isDefault: false,
          isActive: true,
        },
      ],
      ...overrides,
    };
  }

  describe('listCategories', () => {
    it('returns categories ordered by sortOrder then name', async () => {
      const items = [
        { id: 'cat-1', slug: 'personal-care', name: 'Personal Care' },
      ];
      prisma.category.findMany.mockResolvedValue(items);

      const result = await service.listCategories();

      expect(prisma.category.findMany).toHaveBeenCalledWith({
        select: { id: true, slug: true, name: true },
        orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
      });
      expect(result).toEqual({ items });
    });
  });

  describe('listProducts', () => {
    it('defaults to page=1, pageSize=20 with flat pagination fields', async () => {
      prisma.product.findMany.mockResolvedValue([mockProduct()]);
      prisma.product.count.mockResolvedValue(1);

      const result = await service.listProducts({});

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({ skip: 0, take: 20 }),
      );
      expect(result).toMatchObject({ total: 1, page: 1, pageSize: 20 });
      expect(result.items[0]).toMatchObject({
        brand: 'PureNest',
        price: { amountCents: 799, currency: 'USD' },
        availability: AvailabilityStatus.IN_STOCK,
      });
    });

    it('rejects minPriceCents greater than maxPriceCents', async () => {
      await expect(
        service.listProducts({ minPriceCents: 5000, maxPriceCents: 1000 }),
      ).rejects.toBeInstanceOf(BadRequestException);
    });

    it('builds case-insensitive OR filter for q', async () => {
      prisma.product.findMany.mockResolvedValue([]);
      prisma.product.count.mockResolvedValue(0);

      await service.listProducts({ q: 'candle' });

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: expect.arrayContaining([
              { name: { contains: 'candle', mode: 'insensitive' } },
            ]),
          }),
        }),
      );
    });

    it('filters by category slug', async () => {
      prisma.product.findMany.mockResolvedValue([]);
      prisma.product.count.mockResolvedValue(0);

      await service.listProducts({ category: 'home-lifestyle' });

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            category: { slug: 'home-lifestyle' },
          }),
        }),
      );
    });

    it('filters by brand case-insensitively', async () => {
      prisma.product.findMany.mockResolvedValue([]);
      prisma.product.count.mockResolvedValue(0);

      await service.listProducts({ brand: 'PureNest' });

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            brand: { equals: 'PureNest', mode: 'insensitive' },
          }),
        }),
      );
    });

    it('applies price range on active variants', async () => {
      prisma.product.findMany.mockResolvedValue([]);
      prisma.product.count.mockResolvedValue(0);

      await service.listProducts({ minPriceCents: 500, maxPriceCents: 2500 });

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            variants: {
              some: {
                isActive: true,
                priceCents: { gte: 500, lte: 2500 },
              },
            },
          }),
        }),
      );
    });

    it('sorts by min variant price in memory for priceAsc', async () => {
      const cheaper = mockProduct({
        id: 'cheap',
        createdAt: new Date('2026-01-01T00:00:00.000Z'),
        variants: [
          {
            id: 'v-c',
            sku: 'C',
            name: 'Default',
            priceCents: 500,
            currency: 'USD',
            stockQuantity: 5,
            reservedQuantity: 0,
            imageUrl: null,
            isDefault: true,
            isActive: true,
          },
        ],
      });
      const pricier = mockProduct({
        id: 'pricey',
        createdAt: new Date('2026-01-03T00:00:00.000Z'),
      });
      prisma.product.findMany.mockResolvedValue([pricier, cheaper]);

      const result = await service.listProducts({ sort: ProductSort.PRICE_ASC });

      expect(result.items.map((item) => item.id)).toEqual(['cheap', 'pricey']);
    });

    it('post-filters availability without hitting paginated count mismatch', async () => {
      const inStock = mockProduct();
      const outOfStock = mockProduct({
        id: 'prod-2',
        variants: [
          {
            id: 'var-oos',
            sku: 'OOS',
            name: 'Default',
            priceCents: 999,
            currency: 'USD',
            stockQuantity: 0,
            reservedQuantity: 0,
            imageUrl: null,
            isDefault: true,
            isActive: true,
          },
        ],
      });
      prisma.product.findMany.mockResolvedValue([inStock, outOfStock]);

      const result = await service.listProducts({
        availability: AvailabilityFilter.OUT_OF_STOCK,
      });

      expect(result.total).toBe(1);
      expect(result.items[0].id).toBe('prod-2');
      expect(result.items[0].availability).toBe(AvailabilityStatus.OUT_OF_STOCK);
    });
  });

  describe('getProductById', () => {
    it('throws NotFoundException when the product does not exist', async () => {
      prisma.product.findFirst.mockResolvedValue(null);

      await expect(service.getProductById('missing-id')).rejects.toBeInstanceOf(
        NotFoundException,
      );
    });

    it('returns contract-shaped detail with variant stockAvailable', async () => {
      prisma.product.findFirst.mockResolvedValue(mockProduct());

      const result = await service.getProductById('prod-1');

      expect(result).toMatchObject({
        brand: 'PureNest',
        category: { slug: 'personal-care' },
        price: { amountCents: 799, currency: 'USD' },
        availability: AvailabilityStatus.IN_STOCK,
      });
      expect(result.variants[0]).toMatchObject({
        stockAvailable: 16,
        isDefault: true,
      });
    });
  });
});
