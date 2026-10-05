import { INestApplication, ValidationPipe } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { OrderStatus } from '@prisma/client';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

const userId = '11111111-1111-4111-8111-111111111111';
const orderId = '22222222-2222-4222-8222-222222222222';

describe('OrdersController (e2e)', () => {
  let app: INestApplication;
  let jwtService: JwtService;
  let userFindFirst: jest.Mock;
  let orderCount: jest.Mock;
  let orderFindMany: jest.Mock;
  let orderFindFirst: jest.Mock;

  beforeAll(async () => {
    userFindFirst = jest.fn();
    orderCount = jest.fn();
    orderFindMany = jest.fn();
    orderFindFirst = jest.fn();

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        user: { findFirst: userFindFirst },
        order: {
          count: orderCount,
          findMany: orderFindMany,
          findFirst: orderFindFirst,
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

    jwtService = moduleFixture.get(JwtService);
  });

  afterAll(async () => {
    await app?.close();
  });

  function bearerToken(): string {
    return jwtService.sign({ sub: userId, typ: 'access' });
  }

  beforeEach(() => {
    userFindFirst.mockResolvedValue({
      id: userId,
      email: 'shopper@example.com',
      displayName: 'Alex Morgan',
    });
  });

  it('GET /api/v1/orders returns 401 without token', async () => {
    await request(app.getHttpServer()).get('/api/v1/orders').expect(401);
  });

  it('GET /api/v1/orders lists orders for authenticated user', async () => {
    orderCount.mockResolvedValue(1);
    orderFindMany.mockResolvedValue([
      {
        id: orderId,
        orderNumber: 'LUM-260405-DEMO01',
        status: OrderStatus.paid,
        totalCents: 5494,
        currency: 'GBP',
        createdAt: new Date('2026-10-01T09:00:00.000Z'),
      },
    ]);

    const response = await request(app.getHttpServer())
      .get('/api/v1/orders?page=1&pageSize=20')
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(200);

    expect(response.body.total).toBe(1);
    expect(response.body.items[0].orderNumber).toBe('LUM-260405-DEMO01');
    expect(response.body.items[0].customerStatusLabel).toBe('Processing');
  });

  it('GET /api/v1/orders/:orderId returns order detail with tracking', async () => {
    orderFindFirst.mockResolvedValue({
      id: orderId,
      orderNumber: 'LUM-260405-DEMO01',
      userId,
      guestEmail: null,
      status: OrderStatus.fulfilled,
      currency: 'GBP',
      subtotalCents: 4999,
      discountCents: 0,
      shippingCents: 495,
      vatCents: 0,
      totalCents: 5494,
      deliveryOption: 'STANDARD',
      couponId: null,
      shippingAddressId: null,
      shippingAddressSnapshot: {
        fullName: 'Alex Shopper',
        line1: '10 High Street',
        city: 'London',
        postalCode: 'SW1A 1AA',
        country: 'GB',
      },
      idempotencyKey: null,
      stripePaymentIntentId: null,
      carrierName: 'Royal Mail',
      trackingNumber: 'RM123456789GB',
      paidAt: new Date('2026-10-01T10:00:00.000Z'),
      fulfilledAt: new Date('2026-10-02T10:00:00.000Z'),
      deliveredAt: null,
      cancelledAt: null,
      createdAt: new Date('2026-10-01T09:00:00.000Z'),
      updatedAt: new Date('2026-10-02T10:00:00.000Z'),
      items: [
        {
          id: '33333333-3333-4333-8333-333333333333',
          orderId,
          variantId: null,
          productName: 'Modern LED Ceiling Light',
          variantLabel: 'White',
          sku: 'CL-1001-WH',
          quantity: 1,
          unitPriceCents: 4999,
          currency: 'GBP',
          lineTotalCents: 4999,
          createdAt: new Date('2026-10-01T09:00:00.000Z'),
          updatedAt: new Date('2026-10-01T09:00:00.000Z'),
        },
      ],
    });

    const response = await request(app.getHttpServer())
      .get(`/api/v1/orders/${orderId}`)
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(200);

    expect(response.body.tracking.carrierName).toBe('Royal Mail');
    expect(response.body.tracking.trackingNumber).toBe('RM123456789GB');
    expect(response.body.customerStatusLabel).toBe('Shipped');
  });

  it('GET /api/v1/orders/:orderId returns 404 when not found', async () => {
    orderFindFirst.mockResolvedValue(null);

    const response = await request(app.getHttpServer())
      .get(`/api/v1/orders/${orderId}`)
      .set('Authorization', `Bearer ${bearerToken()}`)
      .expect(404);

    expect(response.body.message).toBe('Order not found');
  });
});
