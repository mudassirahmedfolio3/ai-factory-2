import { INestApplication, ValidationPipe } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Decimal } from '@prisma/client/runtime/library';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

const userId = '11111111-1111-4111-8111-111111111111';
const productId = '22222222-2222-4222-8222-222222222222';
const addedAt = new Date('2026-10-04T12:00:00.000Z');

const productWithRelations = {
  id: productId,
  name: 'Modern LED Ceiling Light',
  slug: 'modern-led-ceiling-light',
  primaryImageUrl: 'assets/product.png',
  averageRating: new Decimal('4.5'),
  reviewCount: 12,
  popularityRank: 3,
  isActive: true,
  brand: { name: 'Luminex' },
  category: {
    id: 'c1111111-1111-4111-8111-111111111111',
    name: 'Ceiling',
    slug: 'ceiling-lights',
    parentId: null,
    imageUrl: 'assets/cat.png',
  },
  variants: [
    {
      id: 'v1111111-1111-4111-8111-111111111111',
      sku: 'CL-1001-WH',
      label: 'White',
      priceCents: 4999,
      compareAtCents: null,
      currency: 'GBP',
      stockQuantity: 10,
      reservedQuantity: 0,
      isActive: true,
      isDefault: true,
    },
  ],
};

describe('WishlistController (e2e)', () => {
  let app: INestApplication;
  let jwtService: JwtService;
  let userFindFirst: jest.Mock;
  let wishlistCount: jest.Mock;
  let wishlistFindMany: jest.Mock;
  let wishlistFindUnique: jest.Mock;
  let wishlistCreate: jest.Mock;
  let wishlistDeleteMany: jest.Mock;
  let productFindFirst: jest.Mock;

  beforeAll(async () => {
    userFindFirst = jest.fn();
    wishlistCount = jest.fn();
    wishlistFindMany = jest.fn();
    wishlistFindUnique = jest.fn();
    wishlistCreate = jest.fn();
    wishlistDeleteMany = jest.fn();
    productFindFirst = jest.fn();

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        user: { findFirst: userFindFirst },
        wishlistItem: {
          count: wishlistCount,
          findMany: wishlistFindMany,
          findUnique: wishlistFindUnique,
          create: wishlistCreate,
          deleteMany: wishlistDeleteMany,
        },
        product: { findFirst: productFindFirst },
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

    jwtService = moduleFixture.get(JwtService);
  });

  afterAll(async () => {
    await app?.close();
  });

  function bearerToken(): string {
    return jwtService.sign({ sub: userId, typ: 'access' });
  }

  beforeEach(() => {
    jest.clearAllMocks();
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });
  });

  it('GET /api/v1/wishlist returns 401 without token', async () => {
    await request(app.getHttpServer()).get('/api/v1/wishlist').expect(401);
  });

  it('GET /api/v1/wishlist lists items for authenticated user', async () => {
    wishlistCount.mockResolvedValue(1);
    wishlistFindMany.mockResolvedValue([
      {
        productId,
        createdAt: addedAt,
        product: productWithRelations,
      },
    ]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/wishlist?page=1&pageSize=20')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(200);

    expect(response.body.total).toBe(1);
    expect(response.body.items[0].productId).toBe(productId);
    expect(response.body.items[0].product.name).toBe('Modern LED Ceiling Light');
  });

  it('POST /api/v1/wishlist/items adds item and returns 201', async () => {
    productFindFirst.mockResolvedValue(productWithRelations);
    wishlistFindUnique.mockResolvedValue(null);
    wishlistCreate.mockResolvedValue({
      productId,
      createdAt: addedAt,
      product: productWithRelations,
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/wishlist/items')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .send({ productId })
      .expect(201);

    expect(response.body.productId).toBe(productId);
    expect(response.body.addedAt).toBe(addedAt.toISOString());
  });

  it('POST /api/v1/wishlist/items returns 401 without token', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/wishlist/items')
      .send({ productId })
      .expect(401);
  });

  it('POST /api/v1/wishlist/items returns 404 when product is missing', async () => {
    productFindFirst.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .post('/api/v1/wishlist/items')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .send({ productId })
      .expect(404);

    expect(response.body.message).toBe('Product not found');
  });

  it('POST /api/v1/wishlist/items is idempotent when item already exists', async () => {
    productFindFirst.mockResolvedValue(productWithRelations);
    wishlistFindUnique.mockResolvedValue({
      productId,
      createdAt: addedAt,
      product: productWithRelations,
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/wishlist/items')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .send({ productId })
      .expect(201);

    expect(wishlistCreate).not.toHaveBeenCalled();
    expect(response.body.productId).toBe(productId);
    expect(response.body.addedAt).toBe(addedAt.toISOString());
  });

  it('DELETE /api/v1/wishlist/items/:productId returns 204', async () => {
    wishlistDeleteMany.mockResolvedValue({ count: 1 });

    await request(app.getHttpServer())
      .delete(`/api/v1/wishlist/items/${productId}`)
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(204);
  });

  it('DELETE /api/v1/wishlist/items/:productId returns 404 when missing', async () => {
    wishlistDeleteMany.mockResolvedValue({ count: 0 });

    const response = await request(app.getHttpServer())
      .delete(`/api/v1/wishlist/items/${productId}`)
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(404);

    expect(response.body.message).toBe('Wishlist item not found');
  });
});
