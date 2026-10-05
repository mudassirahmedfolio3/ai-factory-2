import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import {
  collectFinishes,
  listingPriceBounds,
  paginateItems,
  productMatchesListQuery,
  ProductForFiltering,
  sortProductsForListing,
  wattageBounds,
} from './catalog-product.filters';
import { M1_CATALOG_PARITY } from './catalog-seed.constants';
import {
  ProductDetailWithRelations,
  ProductWithRelations,
  toCategorySummary,
  toHomeBannerDto,
  toProductDetail,
  toProductSummary,
  toReviewDto,
} from './catalog.mapper';
import { CatalogFacetsQueryDto } from './dto/catalog-facets-query.dto';
import { CatalogFacetsResponseDto } from './dto/catalog-facets-response.dto';
import { CategoryDetailDto } from './dto/category-detail.dto';
import { CategoryListResponseDto } from './dto/category-list-response.dto';
import { HomeResponseDto } from './dto/home-response.dto';
import { ListProductsQueryDto } from './dto/list-products-query.dto';
import { ProductDetailDto } from './dto/product-detail.dto';
import { ProductListResponseDto } from './dto/product-list-response.dto';
import { ReviewListResponseDto } from './dto/review-list-response.dto';
import { PaginationQueryDto } from './dto/pagination-query.dto';
import { CatalogAnalyticsService } from './catalog-analytics.service';
import { ProductViewAnalyticsContext } from './catalog-analytics.types';

const productSummaryInclude = {
  brand: { select: { name: true } },
  category: {
    select: { id: true, name: true, slug: true, parentId: true, imageUrl: true },
  },
  variants: {
    where: { isActive: true },
    orderBy: [
      { isDefault: Prisma.SortOrder.desc },
      { sku: Prisma.SortOrder.asc },
    ],
  },
} satisfies Prisma.ProductInclude;

const productListInclude = {
  ...productSummaryInclude,
  specs: true,
} satisfies Prisma.ProductInclude;

const productDetailInclude = {
  ...productSummaryInclude,
  specs: true,
  images: { orderBy: { sortOrder: Prisma.SortOrder.asc } },
} satisfies Prisma.ProductInclude;

@Injectable()
export class CatalogService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly catalogAnalytics: CatalogAnalyticsService,
  ) {}

  async getHome(): Promise<HomeResponseDto> {
    const [categories, banners, featuredProducts, newArrivals] =
      await Promise.all([
        this.prisma.category.findMany({
          where: { isActive: true, parentId: null },
          orderBy: { sortOrder: 'asc' },
          select: {
            id: true,
            name: true,
            slug: true,
            parentId: true,
            imageUrl: true,
          },
        }),
        this.prisma.homeBanner.findMany({
          where: { isActive: true },
          orderBy: { sortOrder: 'asc' },
        }),
        this.prisma.product.findMany({
          where: { isActive: true, isFeatured: true },
          orderBy: [{ popularityRank: 'asc' }, { name: 'asc' }],
          take: M1_CATALOG_PARITY.featuredProductCount,
          include: productSummaryInclude,
        }),
        this.prisma.product.findMany({
          where: { isActive: true },
          orderBy: { createdAt: 'desc' },
          take: M1_CATALOG_PARITY.newArrivalProductCount,
          include: productSummaryInclude,
        }),
      ]);

    return {
      categories: categories.map(toCategorySummary),
      banners: banners.map(toHomeBannerDto),
      featuredProducts: featuredProducts.map((product) =>
        toProductSummary(product as ProductWithRelations),
      ),
      newArrivals: newArrivals.map((product) =>
        toProductSummary(product as ProductWithRelations),
      ),
    };
  }

  async listCategories(depth: number): Promise<CategoryListResponseDto> {
    const where =
      depth === 1
        ? { isActive: true, parentId: null }
        : { isActive: true };

    const categories = await this.prisma.category.findMany({
      where,
      orderBy: { sortOrder: 'asc' },
      select: {
        id: true,
        name: true,
        slug: true,
        parentId: true,
        imageUrl: true,
      },
    });

    return { items: categories.map(toCategorySummary) };
  }

  async getCategoryBySlug(slug: string): Promise<CategoryDetailDto> {
    const category = await this.prisma.category.findFirst({
      where: { slug, isActive: true },
      select: {
        id: true,
        name: true,
        slug: true,
        parentId: true,
        imageUrl: true,
        description: true,
      },
    });

    if (!category) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: 'Category not found',
      });
    }

    const children = await this.prisma.category.findMany({
      where: { isActive: true, parentId: category.id },
      orderBy: { sortOrder: 'asc' },
      select: {
        id: true,
        name: true,
        slug: true,
        parentId: true,
        imageUrl: true,
      },
    });

    const detail: CategoryDetailDto = {
      ...toCategorySummary(category),
    };

    if (category.description) {
      detail.description = category.description;
    }

    if (children.length > 0) {
      detail.children = children.map(toCategorySummary);
    }

    return detail;
  }

  async getCatalogFacets(
    query: CatalogFacetsQueryDto,
  ): Promise<CatalogFacetsResponseDto> {
    const categoryIds = query.categorySlug
      ? await this.resolveCategoryScopeIds(query.categorySlug)
      : undefined;

    const products = await this.loadProductsForScope(categoryIds);

    const brandCounts = new Map<string, number>();
    for (const product of products) {
      const name = product.brand.name;
      brandCounts.set(name, (brandCounts.get(name) ?? 0) + 1);
    }

    const brands = [...brandCounts.entries()]
      .map(([name, productCount]) => ({ name, productCount }))
      .sort((a, b) => a.name.localeCompare(b.name));

    const categoryMap = new Map<string, ProductForFiltering['category']>();
    for (const product of products) {
      categoryMap.set(product.category.id, product.category);
    }

    return {
      brands,
      finishes: collectFinishes(products),
      wattage: wattageBounds(products),
      price: listingPriceBounds(products),
      categories: [...categoryMap.values()]
        .map(toCategorySummary)
        .sort((a, b) => a.name.localeCompare(b.name)),
    };
  }

  async listProducts(query: ListProductsQueryDto): Promise<ProductListResponseDto> {
    this.assertValidPriceRange(query.minPriceCents, query.maxPriceCents);
    this.assertValidWattageRange(query.minWattage, query.maxWattage);

    const categoryIds = query.categorySlug
      ? await this.resolveCategoryScopeIds(query.categorySlug)
      : undefined;

    if (query.categorySlug && categoryIds?.length === 0) {
      return {
        items: [],
        total: 0,
        page: query.page,
        pageSize: query.pageSize,
      };
    }

    const products = await this.loadProductsForScope(categoryIds);
    const filtered = products.filter((product) =>
      productMatchesListQuery(product, query, categoryIds),
    );
    const sorted = sortProductsForListing(filtered, query.sort);
    const page = paginateItems(sorted, query.page, query.pageSize);

    return page;
  }

  async getProductById(
    productId: string,
    viewContext?: ProductViewAnalyticsContext,
  ): Promise<ProductDetailDto> {
    const product = await this.prisma.product.findFirst({
      where: { id: productId, isActive: true },
      include: productDetailInclude,
    });

    if (!product) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: 'Product not found',
      });
    }

    const activeVariants = product.variants.filter((v) => v.isActive);
    if (activeVariants.length === 0) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: 'Product not found',
      });
    }

    const detail = toProductDetail(product as ProductDetailWithRelations);
    this.catalogAnalytics.recordProductView(productId, viewContext);
    return detail;
  }

  async listProductReviews(
    productId: string,
    query: PaginationQueryDto,
  ): Promise<ReviewListResponseDto> {
    const product = await this.prisma.product.findFirst({
      where: { id: productId, isActive: true },
      select: {
        id: true,
        averageRating: true,
        reviewCount: true,
      },
    });

    if (!product) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: 'Product not found',
      });
    }

    const skip = (query.page - 1) * query.pageSize;
    const [total, reviews] = await Promise.all([
      this.prisma.review.count({ where: { productId } }),
      this.prisma.review.findMany({
        where: { productId },
        orderBy: { createdAt: 'desc' },
        skip,
        take: query.pageSize,
      }),
    ]);

    return {
      items: reviews.map(toReviewDto),
      total,
      page: query.page,
      pageSize: query.pageSize,
      rating: {
        averageRating: Number(product.averageRating),
        reviewCount: product.reviewCount,
      },
    };
  }

  private assertValidPriceRange(
    minPriceCents?: number,
    maxPriceCents?: number,
  ): void {
    if (
      minPriceCents != null &&
      maxPriceCents != null &&
      minPriceCents > maxPriceCents
    ) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: 'minPriceCents must not exceed maxPriceCents',
      });
    }
  }

  private assertValidWattageRange(
    minWattage?: number,
    maxWattage?: number,
  ): void {
    if (
      minWattage != null &&
      maxWattage != null &&
      minWattage > maxWattage
    ) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: 'minWattage must not exceed maxWattage',
      });
    }
  }

  private async resolveCategoryScopeIds(slug: string): Promise<string[]> {
    const category = await this.prisma.category.findFirst({
      where: { slug, isActive: true },
      select: { id: true },
    });

    if (!category) {
      return [];
    }

    const children = await this.prisma.category.findMany({
      where: { isActive: true, parentId: category.id },
      select: { id: true },
    });

    return [category.id, ...children.map((child) => child.id)];
  }

  private async loadProductsForScope(
    categoryIds: string[] | undefined,
  ): Promise<ProductForFiltering[]> {
    const where: Prisma.ProductWhereInput = { isActive: true };
    if (categoryIds && categoryIds.length > 0) {
      where.categoryId = { in: categoryIds };
    }

    const products = await this.prisma.product.findMany({
      where,
      include: productListInclude,
      orderBy: { name: 'asc' },
    });

    return products as ProductForFiltering[];
  }
}
