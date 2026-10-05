import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import type { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service.js';
import {
  productAvailability,
  toCategoryResponse,
  toProductDetail,
  toProductSummary,
  type CatalogProductRow,
} from './catalog.mapper.js';
import { AvailabilityStatus } from './dto/catalog.responses.js';
import type {
  CategoryListResponse,
  ProductDetailResponse,
  ProductListResponse,
} from './dto/catalog.responses.js';
import {
  AvailabilityFilter,
  type ListProductsQueryDto,
  ProductSort,
} from './dto/list-products.query.js';

const PRODUCT_INCLUDE = {
  category: { select: { id: true, slug: true, name: true } },
  variants: {
    where: { isActive: true },
    orderBy: [{ isDefault: 'desc' as const }, { priceCents: 'asc' as const }],
  },
} satisfies Prisma.ProductInclude;

@Injectable()
export class CatalogService {
  constructor(private readonly prisma: PrismaService) {}

  async listCategories(): Promise<CategoryListResponse> {
    const items = await this.prisma.category.findMany({
      select: { id: true, slug: true, name: true },
      orderBy: [{ sortOrder: 'asc' }, { name: 'asc' }],
    });
    return { items };
  }

  async listProducts(query: ListProductsQueryDto): Promise<ProductListResponse> {
    if (
      query.minPriceCents !== undefined &&
      query.maxPriceCents !== undefined &&
      query.minPriceCents > query.maxPriceCents
    ) {
      throw new BadRequestException(
        'minPriceCents must be less than or equal to maxPriceCents',
      );
    }

    const page = query.page ?? 1;
    const pageSize = query.pageSize ?? 20;
    const skip = (page - 1) * pageSize;
    const lowStockThreshold = await this.getLowStockThreshold();
    const where = this.buildProductsWhere(query);
    const sort = query.sort ?? ProductSort.NEWEST;
    const needsInMemoryOrdering =
      query.availability !== undefined ||
      sort === ProductSort.PRICE_ASC ||
      sort === ProductSort.PRICE_DESC;

    if (needsInMemoryOrdering) {
      const rows = await this.prisma.product.findMany({
        where,
        include: PRODUCT_INCLUDE,
        orderBy: { createdAt: 'desc' },
      });
      let working = rows as CatalogProductRow[];
      if (query.availability !== undefined) {
        working = working.filter(
          (product) =>
            productAvailability(product.variants, lowStockThreshold) ===
            this.toAvailabilityStatus(query.availability!),
        );
      }
      const sorted = this.sortProductsInMemory(working, sort);
      const pageRows = sorted.slice(skip, skip + pageSize);

      return {
        items: pageRows.map((product) =>
          toProductSummary(product, lowStockThreshold),
        ),
        total: sorted.length,
        page,
        pageSize,
      };
    }

    const [rows, total] = await this.prisma.$transaction([
      this.prisma.product.findMany({
        where,
        include: PRODUCT_INCLUDE,
        orderBy: { createdAt: 'desc' },
        skip,
        take: pageSize,
      }),
      this.prisma.product.count({ where }),
    ]);

    return {
      items: (rows as CatalogProductRow[]).map((product) =>
        toProductSummary(product, lowStockThreshold),
      ),
      total,
      page,
      pageSize,
    };
  }

  async getProductById(productId: string): Promise<ProductDetailResponse> {
    const product = await this.prisma.product.findFirst({
      where: { id: productId, isActive: true },
      include: PRODUCT_INCLUDE,
    });

    if (!product) {
      throw new NotFoundException(
        `Product with id '${productId}' was not found`,
      );
    }

    const lowStockThreshold = await this.getLowStockThreshold();
    return toProductDetail(product as CatalogProductRow, lowStockThreshold);
  }

  async getLowStockThreshold(): Promise<number> {
    const config = await this.prisma.storeConfig.findUnique({
      where: { id: 1 },
      select: { lowStockThreshold: true },
    });
    return config?.lowStockThreshold ?? 5;
  }

  mapCategories(
    categories: Array<{ id: string; slug: string; name: string }>,
  ) {
    return categories.map(toCategoryResponse);
  }

  private sortProductsInMemory(
    products: CatalogProductRow[],
    sort: ProductSort,
  ): CatalogProductRow[] {
    const copy = [...products];
    copy.sort((left, right) => {
      if (sort === ProductSort.NEWEST) {
        return right.createdAt.getTime() - left.createdAt.getTime();
      }
      const leftPrice = this.minActiveVariantPrice(left.variants);
      const rightPrice = this.minActiveVariantPrice(right.variants);
      if (sort === ProductSort.PRICE_ASC) {
        return leftPrice - rightPrice || left.name.localeCompare(right.name);
      }
      return rightPrice - leftPrice || left.name.localeCompare(right.name);
    });
    return copy;
  }

  private buildProductsWhere(
    query: ListProductsQueryDto,
  ): Prisma.ProductWhereInput {
    const where: Prisma.ProductWhereInput = { isActive: true };

    if (query.q !== undefined) {
      where.OR = [
        { name: { contains: query.q, mode: 'insensitive' } },
        { description: { contains: query.q, mode: 'insensitive' } },
        { brand: { contains: query.q, mode: 'insensitive' } },
        {
          variants: {
            some: { sku: { contains: query.q, mode: 'insensitive' } },
          },
        },
      ];
    }

    if (query.category !== undefined) {
      where.category = { slug: query.category };
    }

    if (query.brand !== undefined) {
      where.brand = { equals: query.brand, mode: 'insensitive' };
    }

    if (query.minPriceCents !== undefined || query.maxPriceCents !== undefined) {
      where.variants = {
        some: {
          isActive: true,
          priceCents: {
            ...(query.minPriceCents !== undefined
              ? { gte: query.minPriceCents }
              : {}),
            ...(query.maxPriceCents !== undefined
              ? { lte: query.maxPriceCents }
              : {}),
          },
        },
      };
    }

    return where;
  }

  private minActiveVariantPrice(
    variants: CatalogProductRow['variants'],
  ): number {
    if (variants.length === 0) {
      return Number.MAX_SAFE_INTEGER;
    }
    return Math.min(...variants.map((variant) => variant.priceCents));
  }

  private toAvailabilityStatus(
    filter: AvailabilityFilter,
  ): AvailabilityStatus {
    switch (filter) {
      case AvailabilityFilter.IN_STOCK:
        return AvailabilityStatus.IN_STOCK;
      case AvailabilityFilter.LOW_STOCK:
        return AvailabilityStatus.LOW_STOCK;
      case AvailabilityFilter.OUT_OF_STOCK:
        return AvailabilityStatus.OUT_OF_STOCK;
      default:
        return AvailabilityStatus.IN_STOCK;
    }
  }
}
