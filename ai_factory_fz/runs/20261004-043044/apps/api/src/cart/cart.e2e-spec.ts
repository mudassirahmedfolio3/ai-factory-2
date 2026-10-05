import { INestApplication, ValidationPipe } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';
import { INSUFFICIENT_STOCK_MESSAGE } from './cart.constants';

const userId = '11111111-1111-4111-8111-111111111111';
const cartId = 'c1111111-1111-4111-8111-111111111111';
const guestCartId = 'a1111111-1111-4111-8111-111111111111';
const variantId = 'b1111111-1111-4111-8111-111111111111';
const itemId = 'd1111111-1111-4111-8111-111111111111';

describe('CartController (e2e)', () => {
  let app: INestApplication;
  let jwtService: JwtService;
  let cartFindUnique: jest.Mock;
  let cartCreate: jest.Mock;
  let cartItemCreate: jest.Mock;
  let cartItemUpdate: jest.Mock;
  let cartItemDelete: jest.Mock;
  let cartItemFindUnique: jest.Mock;
  let guestCartFindUnique: jest.Mock;
  let guestCartCreate: jest.Mock;
  let guestCartUpdate: jest.Mock;
  let guestCartDelete: jest.Mock;
  let guestCartItemCreate: jest.Mock;
  let guestCartItemUpdate: jest.Mock;
  let guestCartItemDelete: jest.Mock;
  let productVariantFindFirst: jest.Mock;
  let userFindFirst: jest.Mock;
  let transaction: jest.Mock;

  const variant = {
    id: variantId,
    productId: 'p1111111-1111-4111-8111-111111111111',
    sku: 'CL-1001-WH',
    label: 'White',
    priceCents: 4999,
    currency: 'GBP',
    stockQuantity: 10,
    reservedQuantity: 0,
    imageUrl: 'assets/variant.png',
    isActive: true,
    product: {
      id: 'p1111111-1111-4111-8111-111111111111',
      name: 'Modern LED Ceiling Light',
      primaryImageUrl: 'assets/product.png',
      isActive: true,
    },
  };

  beforeAll(async () => {
    cartFindUnique = jest.fn();
    cartCreate = jest.fn();
    cartItemCreate = jest.fn();
    cartItemUpdate = jest.fn();
    cartItemDelete = jest.fn();
    cartItemFindUnique = jest.fn();
    guestCartFindUnique = jest.fn();
    guestCartCreate = jest.fn();
    guestCartUpdate = jest.fn();
    guestCartDelete = jest.fn();
    guestCartItemCreate = jest.fn();
    guestCartItemUpdate = jest.fn();
    guestCartItemDelete = jest.fn();
    productVariantFindFirst = jest.fn();
    userFindFirst = jest.fn();
    transaction = jest.fn(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        productVariant: { findFirst: productVariantFindFirst },
        cartItem: {
          findUnique: cartItemFindUnique,
          update: cartItemUpdate,
          create: cartItemCreate,
        },
        guestCart: { delete: guestCartDelete },
      }),
    );

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        user: { findFirst: userFindFirst },
        cart: {
          findUnique: cartFindUnique,
          create: cartCreate,
        },
        cartItem: {
          create: cartItemCreate,
          update: cartItemUpdate,
          delete: cartItemDelete,
          findUnique: cartItemFindUnique,
        },
        guestCart: {
          findUnique: guestCartFindUnique,
          create: guestCartCreate,
          update: guestCartUpdate,
          delete: guestCartDelete,
        },
        guestCartItem: {
          create: guestCartItemCreate,
          update: guestCartItemUpdate,
          delete: guestCartItemDelete,
        },
        productVariant: {
          findFirst: productVariantFindFirst,
        },
        $transaction: transaction,
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

  function authHeader(): string {
    const token = jwtService.sign({ sub: userId, typ: 'access' });
    return `Bearer ${token}`;
  }

  it('getCart — GET /api/v1/cart creates guest cart when anonymous', async () => {
    guestCartCreate.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [],
    });

    const response = await request(app.getHttpServer()).get('/api/v1/cart').expect(200);

    expect(response.body.guestCartId).toBe(guestCartId);
    expect(response.body.itemCount).toBe(0);
  });

  it('addCartItem — POST /api/v1/cart/items returns updated cart', async () => {
    const guestLine = {
      id: itemId,
      guestCartId,
      variantId,
      quantity: 1,
      unitPriceCents: 4999,
      currency: 'GBP',
      productName: variant.product.name,
      variantLabel: variant.label,
      sku: variant.sku,
      variant,
    };
    let guestItems: typeof guestLine[] = [];

    guestCartUpdate.mockResolvedValue({});
    guestCartFindUnique.mockImplementation(async () => ({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: guestItems,
    }));
    guestCartItemCreate.mockImplementation(async () => {
      guestItems = [guestLine];
      return guestLine;
    });
    productVariantFindFirst.mockResolvedValue(variant);

    const response = await request(app.getHttpServer())
      .post('/api/v1/cart/items')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({ variantId, quantity: 1 })
      .expect(200);

    expect(response.body.subtotalCents).toBe(4999);
    expect(response.body.items[0].imageUrl).toBe('assets/variant.png');
  });

  it('updateCartItem — PATCH /api/v1/cart/items/{itemId} rejects quantity above stock', async () => {
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex',
    });
    cartFindUnique.mockResolvedValue({
      id: cartId,
      userId,
      items: [
        {
          id: itemId,
          cartId,
          variantId,
          quantity: 1,
          unitPriceCents: 4999,
          currency: 'GBP',
          productName: variant.product.name,
          variantLabel: variant.label,
          sku: variant.sku,
          variant,
        },
      ],
    });
    productVariantFindFirst.mockResolvedValue({
      ...variant,
      stockQuantity: 2,
      reservedQuantity: 0,
    });

    const response = await request(app.getHttpServer())
      .patch(`/api/v1/cart/items/${itemId}`)
      .set('Authorization', authHeader())
      .send({ quantity: 3 })
      .expect(409);

    expect(response.body).toMatchObject({
      statusCode: 409,
      error: 'Conflict',
      message: INSUFFICIENT_STOCK_MESSAGE,
    });
    expect(cartItemUpdate).not.toHaveBeenCalled();
  });

  it('mergeGuestCart — POST /api/v1/cart/merge requires auth', async () => {
    await request(app.getHttpServer()).post('/api/v1/cart/merge').expect(401);
  });

  it('mergeGuestCart — merges when authenticated', async () => {
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex',
    });
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [
        {
          id: 'g-item',
          guestCartId,
          variantId,
          quantity: 1,
          unitPriceCents: 4999,
          currency: 'GBP',
          productName: variant.product.name,
          variantLabel: variant.label,
          sku: variant.sku,
        },
      ],
    });
    cartFindUnique
      .mockResolvedValueOnce({
        id: cartId,
        userId,
        items: [],
      })
      .mockResolvedValueOnce({
        id: cartId,
        userId,
        items: [
          {
            id: itemId,
            cartId,
            variantId,
            quantity: 1,
            unitPriceCents: 4999,
            currency: 'GBP',
            productName: variant.product.name,
            variantLabel: variant.label,
            sku: variant.sku,
            variant,
          },
        ],
      });
    productVariantFindFirst.mockResolvedValue(variant);
    cartItemFindUnique.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .post('/api/v1/cart/merge')
      .set('Authorization', authHeader())
      .set('X-Guest-Cart-Id', guestCartId)
      .expect(200);

    expect(response.body.id).toBe(cartId);
    expect(response.body.itemCount).toBe(1);
  });
});
