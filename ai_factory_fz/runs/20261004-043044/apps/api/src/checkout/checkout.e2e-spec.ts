import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

const guestCartId = 'a1111111-1111-4111-8111-111111111111';
const variantId = 'b1111111-1111-4111-8111-111111111111';
const itemId = 'd1111111-1111-4111-8111-111111111111';

describe('CheckoutController (e2e)', () => {
  let app: INestApplication;
  let guestCartFindUnique: jest.Mock;
  let checkoutIdempotencyFindUnique: jest.Mock;
  let transaction: jest.Mock;
  let couponFindFirst: jest.Mock;
  let productVariantFindMany: jest.Mock;

  const ceilingCategoryId = 'c1111111-1111-4111-8111-111111111101';
  const outdoorCategoryId = 'c1111111-1111-4111-8111-111111111102';

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

  const previewBody = {
    shippingAddress: {
      fullName: 'Alex Smith',
      line1: '10 High Street',
      city: 'London',
      postalCode: 'SW1A 1AA',
      country: 'GB',
    },
  };

  const createOrderBody = {
    ...previewBody,
    contactEmail: 'shopper@example.com',
  };

  beforeAll(async () => {
    guestCartFindUnique = jest.fn();
    checkoutIdempotencyFindUnique = jest.fn().mockResolvedValue(null);
    transaction = jest.fn();
    couponFindFirst = jest.fn();
    productVariantFindMany = jest.fn();

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        cart: { findUnique: jest.fn() },
        guestCart: { findUnique: guestCartFindUnique },
        checkoutIdempotency: { findUnique: checkoutIdempotencyFindUnique },
        coupon: { findFirst: couponFindFirst },
        productVariant: { findMany: productVariantFindMany },
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
  });

  afterAll(async () => {
    await app?.close();
  });

  it('POST /api/v1/checkout/preview returns preview totals', async () => {
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [guestLine],
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send(previewBody)
      .expect(200);

    expect(response.body).toMatchObject({
      subtotalCents: 4999,
      shippingCents: 495,
      discountCents: 0,
      totalCents: 5494,
      currency: 'GBP',
      freeDeliveryThresholdCents: 7500,
      couponApplied: false,
      shippingLabel: 'Standard UK domestic delivery only',
    });
  });

  it('POST /api/v1/checkout/preview applies free shipping at threshold', async () => {
    const highValueLine = {
      ...guestLine,
      quantity: 2,
      unitPriceCents: 3750,
    };

    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [highValueLine],
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send(previewBody)
      .expect(200);

    expect(response.body).toMatchObject({
      subtotalCents: 7500,
      shippingCents: 0,
      discountCents: 0,
      totalCents: 7500,
      currency: 'GBP',
      freeDeliveryThresholdCents: 7500,
      couponApplied: false,
      shippingLabel: 'Free standard UK domestic delivery',
    });
  });

  it('POST /api/v1/checkout/preview rejects invalid country', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({
        shippingAddress: { ...previewBody.shippingAddress, country: 'US' },
      })
      .expect(400);
  });

  it('POST /api/v1/checkout/preview returns 422 for empty guest cart', async () => {
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [],
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send(previewBody)
      .expect(422);

    expect(response.body.message).toBe('Cart is empty or not found');
  });

  it('POST /api/v1/checkout/preview applies valid coupon with discount in pence', async () => {
    const ceilingLine = {
      ...guestLine,
      unitPriceCents: 6000,
      variant: {
        ...variant,
        compareAtCents: null,
        product: {
          ...variant.product,
          categoryId: ceilingCategoryId,
        },
      },
    };

    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [ceilingLine],
    });

    couponFindFirst.mockResolvedValue({
      id: 'cp111111-1111-4111-8111-111111111101',
      code: 'CEILING10',
      description: '10% off ceiling lighting',
      percentOff: 10,
      amountOffCents: null,
      currency: 'GBP',
      minSubtotalCents: 5000,
      expiresAt: new Date('2027-01-01T00:00:00.000Z'),
      singleUsePerEmail: false,
      excludeSaleItems: true,
      isActive: true,
      categories: [{ categoryId: ceilingCategoryId }],
      products: [],
    });

    productVariantFindMany.mockResolvedValue([
      {
        id: variantId,
        compareAtCents: null,
        product: { id: variant.product.id, categoryId: ceilingCategoryId },
      },
    ]);

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({ ...previewBody, couponCode: 'CEILING10' })
      .expect(200);

    expect(response.body).toMatchObject({
      subtotalCents: 6000,
      shippingCents: 495,
      discountCents: 600,
      totalCents: 5895,
      currency: 'GBP',
      couponApplied: true,
      couponCode: 'CEILING10',
      couponMessage: '10% off ceiling lighting',
    });
  });

  it('POST /api/v1/checkout/preview rejects stacked coupon codes', async () => {
    couponFindFirst.mockClear();
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [guestLine],
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({ ...previewBody, couponCode: 'CEILING10, OUTDOOR15' })
      .expect(400);

    expect(response.body.message).toBe('Only one coupon code is allowed per order');
    expect(couponFindFirst).not.toHaveBeenCalled();
  });

  it('POST /api/v1/checkout/preview rejects coupon when cart items are ineligible', async () => {
    const outdoorLine = {
      ...guestLine,
      unitPriceCents: 6000,
      variant: {
        ...variant,
        compareAtCents: null,
        product: {
          ...variant.product,
          categoryId: outdoorCategoryId,
        },
      },
    };

    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [outdoorLine],
    });

    couponFindFirst.mockResolvedValue({
      id: 'cp111111-1111-4111-8111-111111111101',
      code: 'CEILING10',
      description: '10% off ceiling lighting',
      percentOff: 10,
      amountOffCents: null,
      currency: 'GBP',
      minSubtotalCents: 5000,
      expiresAt: new Date('2027-01-01T00:00:00.000Z'),
      singleUsePerEmail: false,
      excludeSaleItems: true,
      isActive: true,
      categories: [{ categoryId: ceilingCategoryId }],
      products: [],
    });

    productVariantFindMany.mockResolvedValue([
      {
        id: variantId,
        compareAtCents: null,
        product: { id: variant.product.id, categoryId: outdoorCategoryId },
      },
    ]);

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({ ...previewBody, couponCode: 'CEILING10' })
      .expect(400);

    expect(response.body.message).toBe(
      'This coupon does not apply to the items in your cart',
    );
  });

  it('POST /api/v1/checkout/preview returns 400 for non-mainland postcode', async () => {
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [guestLine],
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/preview')
      .set('X-Guest-Cart-Id', guestCartId)
      .send({
        shippingAddress: { ...previewBody.shippingAddress, postalCode: 'BT1 1AA' },
      })
      .expect(400);

    expect(response.body.message).toContain('mainland');
  });

  it('POST /api/v1/checkout/orders requires Idempotency-Key', async () => {
    await request(app.getHttpServer())
      .post('/api/v1/checkout/orders')
      .set('X-Guest-Cart-Id', guestCartId)
      .send(createOrderBody)
      .expect(400);
  });

  it('POST /api/v1/checkout/orders creates pending_payment order', async () => {
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [guestLine],
    });

    const paymentExpiresAt = new Date(Date.now() + 900_000);
    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<unknown>) =>
      fn({
        productVariant: {
          findUnique: jest.fn().mockResolvedValue({
            id: variantId,
            isActive: true,
            stockQuantity: 10,
            reservedQuantity: 0,
          }),
          update: jest.fn(),
        },
        order: {
          create: jest.fn().mockResolvedValue({
            id: 'e1111111-1111-4111-8111-111111111111',
            orderNumber: 'LUM-260405-ABC123',
            status: 'pending_payment',
            totalCents: 5494,
            currency: 'GBP',
            mockPaymentSession: {
              id: 'f1111111-1111-4111-8111-111111111111',
              expiresAt: paymentExpiresAt,
            },
          }),
        },
        guestCartItem: { deleteMany: jest.fn() },
      }),
    );

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/orders')
      .set('X-Guest-Cart-Id', guestCartId)
      .set('Idempotency-Key', 'checkout-attempt-1')
      .send(createOrderBody)
      .expect(201);

    expect(response.body).toMatchObject({
      orderNumber: 'LUM-260405-ABC123',
      status: 'pending_payment',
      totalCents: 5494,
      currency: 'GBP',
      mockPaymentSessionId: 'f1111111-1111-4111-8111-111111111111',
    });
  });

  it('POST /api/v1/checkout/orders returns same order for repeated Idempotency-Key', async () => {
    transaction.mockClear();
    const expiresAt = new Date(Date.now() + 900_000);
    checkoutIdempotencyFindUnique.mockResolvedValue({
      order: {
        id: 'e1111111-1111-4111-8111-111111111111',
        orderNumber: 'LUM-260405-ABC123',
        status: 'pending_payment',
        totalCents: 5494,
        currency: 'GBP',
        mockPaymentSession: {
          id: 'f1111111-1111-4111-8111-111111111111',
          expiresAt,
        },
      },
    });

    const response = await request(app.getHttpServer())
      .post('/api/v1/checkout/orders')
      .set('X-Guest-Cart-Id', guestCartId)
      .set('Idempotency-Key', 'checkout-attempt-1')
      .send(createOrderBody)
      .expect(201);

    expect(response.body.orderId).toBe('e1111111-1111-4111-8111-111111111111');
    expect(transaction).not.toHaveBeenCalled();
  });
});
