import { Injectable } from '@nestjs/common';
import type { Prisma } from '@prisma/client';
import { CatalogService } from '../catalog/catalog.service.js';
import {
  toProductSummary,
  type CatalogProductRow,
} from '../catalog/catalog.mapper.js';
import { PrismaService } from '../prisma/prisma.service.js';
import type { HomeResponse } from './dto/home.responses.js';

const PRODUCT_INCLUDE = {
  category: { select: { id: true, slug: true, name: true } },
  variants: {
    where: { isActive: true },
    orderBy: [{ isDefault: 'desc' as const }, { priceCents: 'asc' as const }],
  },
} satisfies Prisma.ProductInclude;

@Injectable()
export class HomeService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly catalogService: CatalogService,
  ) {}

  async getHome(): Promise<HomeResponse> {
    const lowStockThreshold = await this.catalogService.getLowStockThreshold();

    const [banners, featuredRows, newArrivalRows, categories] =
      await Promise.all([
        this.prisma.homeBanner.findMany({
          where: { isActive: true },
          orderBy: [{ sortOrder: 'asc' }, { title: 'asc' }],
          select: {
            id: true,
            title: true,
            subtitle: true,
            imageUrl: true,
            ctaLabel: true,
            categorySlug: true,
          },
        }),
        this.fetchMerchandisedProducts({ isFeatured: true }),
        this.fetchMerchandisedProducts({ isNewArrival: true }),
        this.catalogService.listCategories(),
      ]);

    return {
      banners: banners.map((banner) => ({
        id: banner.id,
        title: banner.title,
        ...(banner.subtitle ? { subtitle: banner.subtitle } : {}),
        imageUrl: banner.imageUrl,
        ...(banner.ctaLabel ? { ctaLabel: banner.ctaLabel } : {}),
        ...(banner.categorySlug ? { categorySlug: banner.categorySlug } : {}),
      })),
      featured: featuredRows.map((product) =>
        toProductSummary(product, lowStockThreshold),
      ),
      newArrivals: newArrivalRows.map((product) =>
        toProductSummary(product, lowStockThreshold),
      ),
      categories: categories.items,
    };
  }

  private async fetchMerchandisedProducts(
    flags: { isFeatured: boolean } | { isNewArrival: boolean },
  ): Promise<CatalogProductRow[]> {
    return this.prisma.product.findMany({
      where: { isActive: true, ...flags },
      include: PRODUCT_INCLUDE,
      orderBy: { createdAt: 'desc' },
    }) as Promise<CatalogProductRow[]>;
  }
}
