import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CatalogService } from '../catalog/catalog.service.js';
import { HomeService } from './home.service.js';

describe('HomeService', () => {
  const prisma = {
    homeBanner: { findMany: vi.fn() },
    product: { findMany: vi.fn() },
  };
  const catalogService = {
    getLowStockThreshold: vi.fn(),
    listCategories: vi.fn(),
  };
  let service: HomeService;

  beforeEach(() => {
    vi.resetAllMocks();
    catalogService.getLowStockThreshold.mockResolvedValue(5);
    catalogService.listCategories.mockResolvedValue({
      items: [{ id: 'cat-1', slug: 'personal-care', name: 'Personal Care' }],
    });
    prisma.homeBanner.findMany.mockResolvedValue([
      {
        id: 'banner-1',
        title: 'Gift-ready favorites',
        subtitle: 'Curated boxes',
        imageUrl: 'https://example.com/banner.jpg',
        ctaLabel: 'Browse gifts',
        categorySlug: 'gift-friendly',
      },
    ]);
    prisma.product.findMany.mockResolvedValue([]);
    service = new HomeService(prisma as never, catalogService as unknown as CatalogService);
  });

  it('aggregates banners, featured, new arrivals, and categories', async () => {
    const featuredProduct = {
      id: 'prod-f',
      name: 'Featured',
      brand: 'PureNest',
      description: 'd',
      primaryImageUrl: 'https://example.com/f.jpg',
      createdAt: new Date(),
      category: { id: 'cat-1', slug: 'personal-care', name: 'Personal Care' },
      variants: [
        {
          id: 'v1',
          sku: 'SKU',
          name: 'Default',
          priceCents: 999,
          currency: 'USD',
          stockQuantity: 10,
          reservedQuantity: 0,
          imageUrl: null,
          isDefault: true,
          isActive: true,
        },
      ],
    };
    prisma.product.findMany
      .mockResolvedValueOnce([featuredProduct])
      .mockResolvedValueOnce([]);

    const result = await service.getHome();

    expect(result.banners).toHaveLength(1);
    expect(result.featured).toHaveLength(1);
    expect(result.featured[0].price).toEqual({
      amountCents: 999,
      currency: 'USD',
    });
    expect(result.newArrivals).toEqual([]);
    expect(result.categories).toHaveLength(1);
    expect(prisma.homeBanner.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: { isActive: true } }),
    );
  });
});
