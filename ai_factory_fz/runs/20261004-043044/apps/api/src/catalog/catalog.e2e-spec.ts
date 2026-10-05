import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { Decimal } from '@prisma/client/runtime/library';
import request from 'supertest';
import { AppModule } from '../app.module';
import { M1_CATALOG_PARITY } from './catalog-seed.constants';
import { PrismaService } from '../prisma/prisma.service';

const rootCategory = {
  id: 'c1111111-1111-4111-8111-111111111101',
  name: 'Ceiling Lights',
  slug: 'ceiling-lights',
  parentId: null,
  imageUrl: 'assets/images/products/placeholder.png',
  description: 'Ceiling range',
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
  id: '11111111-1111-4111-8111-111111111101',
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
    },
  ],
};

describe('CatalogController (e2e)', () => {
  let app: INestApplication;
  let categoryFindMany: jest.Mock;
  let categoryFindFirst: jest.Mock;
  let homeBannerFindMany: jest.Mock;
  let productFindMany: jest.Mock;
  let productFindFirst: jest.Mock;
  let reviewCount: jest.Mock;
  let reviewFindMany: jest.Mock;

  beforeAll(async () => {
    categoryFindMany = jest.fn();
    categoryFindFirst = jest.fn();
    homeBannerFindMany = jest.fn();
    productFindMany = jest.fn();
    productFindFirst = jest.fn();
    reviewCount = jest.fn();
    reviewFindMany = jest.fn();

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn().mockResolvedValue(undefined),
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
      })
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api/v1');
    app.useGlobalPipes(
      new ValidationPipe({
        whitelist: true,
        forbidNonWhitelisted: true,
        transform: true,
      }),
    );
    await app.init();
  });

  afterAll(async () => {
    await app?.close();
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('getHome — GET /api/v1/home returns merchandising payload with GBP pence', async () => {
    categoryFindMany.mockResolvedValue([rootCategory]);
    homeBannerFindMany.mockResolvedValue([
      {
        id: 'h1111111-1111-4111-8111-111111111101',
        title: 'Winter Lighting Sale',
        subtitle: 'Save on ceiling fixtures',
        imageUrl: 'assets/images/banners/winter-sale.png',
        ctaLabel: 'Shop now',
        categorySlug: 'ceiling-lights',
        sortOrder: 1,
        isActive: true,
      },
    ]);
    productFindMany
      .mockResolvedValueOnce([featuredProduct])
      .mockResolvedValueOnce([featuredProduct]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/home')
      .expect(200);

    expect(response.body.categories).toHaveLength(1);
    expect(response.body.banners).toHaveLength(1);
    expect(response.body.banners[0].ctaLabel).toBe('Shop now');
    expect(response.body.featuredProducts).toHaveLength(1);
    expect(response.body.featuredProducts[0].price).toEqual({
      amountCents: 4999,
      currency: 'GBP',
    });
    expect(response.body.featuredProducts[0].brand).toBe('Luminex');
    expect(response.body.newArrivals).toHaveLength(1);
  });

  it('listCategories — GET /api/v1/categories returns flat category list', async () => {
    categoryFindMany.mockResolvedValue([rootCategory, childCategory]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/categories')
      .expect(200);

    expect(response.body.items).toHaveLength(2);
    expect(response.body.items[1].slug).toBe('pendant-lights');
  });

  it('listCategories — GET /api/v1/categories?depth=1 returns top-level only', async () => {
    categoryFindMany.mockResolvedValue([rootCategory]);

    await request(app.getHttpServer())
      .get('/api/v1/categories')
      .query({ depth: 1 })
      .expect(200);

    expect(categoryFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { isActive: true, parentId: null },
      }),
    );
  });

  it('getCategoryBySlug — GET /api/v1/categories/:slug returns category detail with children', async () => {
    categoryFindFirst.mockResolvedValue(rootCategory);
    categoryFindMany.mockResolvedValue([childCategory]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/categories/ceiling-lights')
      .expect(200);

    expect(response.body.slug).toBe('ceiling-lights');
    expect(response.body.children).toHaveLength(1);
    expect(response.body.children[0].slug).toBe('pendant-lights');
  });

  it('getCategoryBySlug — GET /api/v1/categories/:slug returns 404 when not found', async () => {
    categoryFindFirst.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .get('/api/v1/categories/unknown-category')
      .expect(404);

    expect(response.body).toMatchObject({
      statusCode: 404,
      error: 'Not Found',
      message: 'Category not found',
    });
  });

  it('getCatalogFacets — GET /api/v1/catalog/facets returns facet metadata', async () => {
    productFindMany.mockResolvedValue([
      {
        ...featuredProduct,
        description: 'Desc',
        unitsSold90Days: 10,
        createdAt: new Date(),
        specs: { wattageW: 24, finish: 'Matte White' },
      },
    ]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/catalog/facets')
      .expect(200);

    expect(response.body.brands[0]).toEqual({
      name: 'Luminex',
      productCount: 1,
    });
    expect(response.body.price.minPriceCents).toBe(4999);
  });

  it('listProducts — GET /api/v1/products supports search and pagination envelope', async () => {
    productFindMany.mockResolvedValue([
      {
        ...featuredProduct,
        description: 'Modern LED ceiling',
        unitsSold90Days: 10,
        createdAt: new Date(),
        specs: null,
      },
    ]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/products')
      .query({ q: 'Modern LED', page: 1, pageSize: 10 })
      .expect(200);

    expect(response.body.total).toBe(1);
    expect(response.body.page).toBe(1);
    expect(response.body.pageSize).toBe(10);
    expect(response.body.items[0].price.currency).toBe('GBP');
  });

  it('getProductById — GET /api/v1/products/:productId returns detail payload', async () => {
    productFindFirst.mockResolvedValue({
      ...featuredProduct,
      description: 'Detailed description',
      unitsSold90Days: 12,
      specs: { wattageW: 24, lumens: 2400, ipRating: 'IP44' },
      images: [{ url: 'assets/gallery.png', sortOrder: 0, altText: null }],
      variants: [
        {
          id: 'v1111111-1111-4111-8111-111111111101',
          sku: 'CL-1001-WH',
          label: 'White finish',
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

    const response = await request(app.getHttpServer())
      .get(`/api/v1/products/${featuredProduct.id}`)
      .expect(200);

    expect(response.body.variants).toHaveLength(1);
    expect(response.body.specs.wattageW).toBe(24);
    expect(response.body.rating.reviewCount).toBe(12);
  });

  it('getProductById — GET /api/v1/products/:productId returns 404 when not found', async () => {
    productFindFirst.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .get('/api/v1/products/00000000-0000-4000-8000-000000000099')
      .expect(404);

    expect(response.body).toMatchObject({
      statusCode: 404,
      error: 'Not Found',
      message: 'Product not found',
    });
  });

  it('getProductById — GET /api/v1/products/:productId returns 400 for non-UUID id', async () => {
    const response = await request(app.getHttpServer())
      .get('/api/v1/products/not-a-valid-uuid')
      .expect(400);

    expect(response.body).toMatchObject({
      statusCode: 400,
      error: 'Bad Request',
    });
  });

  it('listProductReviews — GET /api/v1/products/:productId/reviews returns paginated reviews', async () => {
    productFindFirst.mockResolvedValue({
      id: featuredProduct.id,
      averageRating: featuredProduct.averageRating,
      reviewCount: 1,
    });
    reviewCount.mockResolvedValue(1);
    reviewFindMany.mockResolvedValue([
      {
        id: 'r1111111-1111-4111-8111-111111111101',
        rating: 5,
        title: 'Excellent',
        body: 'Bright and easy to fit',
        authorDisplayName: 'Verified Buyer',
        createdAt: new Date('2025-08-01T10:00:00.000Z'),
      },
    ]);

    const response = await request(app.getHttpServer())
      .get(`/api/v1/products/${featuredProduct.id}/reviews`)
      .query({ page: 1, pageSize: 5 })
      .expect(200);

    expect(response.body.items).toHaveLength(1);
    expect(response.body.rating.reviewCount).toBe(1);
  });

  it('listProductReviews — returns 404 when product is missing', async () => {
    productFindFirst.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .get(`/api/v1/products/${featuredProduct.id}/reviews`)
      .expect(404);

    expect(response.body).toMatchObject({
      statusCode: 404,
      error: 'Not Found',
      message: 'Product not found',
    });
  });

  it('documents M1 featured product count for merchandising parity', () => {
    expect(M1_CATALOG_PARITY.featuredProductCount).toBe(4);
  });
});
