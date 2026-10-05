import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { AppModule } from '../app.module';
import { PrismaService } from '../prisma/prisma.service';

const orderId = '11111111-1111-4111-8111-111111111111';
const sessionId = '22222222-2222-4222-8222-222222222222';

describe('PaymentsController (e2e)', () => {
  let app: INestApplication;
  let orderFindUnique: jest.Mock;
  let transaction: jest.Mock;

  beforeAll(async () => {
    orderFindUnique = jest.fn();
    transaction = jest.fn(async (fn: (tx: unknown) => Promise<void>) => fn({}));

    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(PrismaService)
      .useValue({
        onModuleInit: jest.fn().mockResolvedValue(undefined),
        onModuleDestroy: jest.fn().mockResolvedValue(undefined),
        pingDatabase: jest.fn(),
        order: { findUnique: orderFindUnique },
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

  it('POST /api/v1/payments/mock/confirm returns 402 on failure', async () => {
    orderFindUnique.mockResolvedValue({
      id: orderId,
      orderNumber: 'LUM-260405-ABC123',
      userId: null,
      status: 'pending_payment',
      paidAt: null,
      mockPaymentSession: {
        id: sessionId,
        expiresAt: new Date(Date.now() + 60_000),
        consumedAt: null,
      },
      payment: { status: 'requires_confirmation' },
      items: [],
      reservations: [],
    });

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        stockReservation: { findMany: jest.fn().mockResolvedValue([]) },
        payment: { update: jest.fn() },
      }),
    );

    const response = await request(app.getHttpServer())
      .post('/api/v1/payments/mock/confirm')
      .send({
        orderId,
        mockPaymentSessionId: sessionId,
        outcome: 'failure',
      })
      .expect(402);

    expect(response.body.message).toContain('Mock payment');
  });

  it('POST /api/v1/payments/mock/confirm marks order paid on success', async () => {
    orderFindUnique.mockResolvedValue({
      id: orderId,
      orderNumber: 'LUM-260405-ABC123',
      userId: null,
      status: 'pending_payment',
      paidAt: null,
      mockPaymentSession: {
        id: sessionId,
        expiresAt: new Date(Date.now() + 60_000),
        consumedAt: null,
      },
      payment: { status: 'requires_confirmation' },
      items: [
        {
          variantId: '33333333-3333-4333-8333-333333333333',
          quantity: 1,
        },
      ],
      reservations: [
        {
          id: '44444444-4444-4444-8444-444444444444',
          variantId: '33333333-3333-4333-8333-333333333333',
          quantity: 1,
          releasedAt: null,
        },
      ],
    });

    transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        stockReservation: {
          findMany: jest.fn().mockResolvedValue([
            {
              id: '44444444-4444-4444-8444-444444444444',
              variantId: '33333333-3333-4333-8333-333333333333',
              quantity: 1,
              releasedAt: null,
            },
          ]),
          update: jest.fn(),
        },
        productVariant: { update: jest.fn() },
        mockPaymentSession: { update: jest.fn() },
        payment: { update: jest.fn() },
        order: { update: jest.fn() },
      }),
    );

    const response = await request(app.getHttpServer())
      .post('/api/v1/payments/mock/confirm')
      .send({
        orderId,
        mockPaymentSessionId: sessionId,
        outcome: 'success',
      })
      .expect(200);

    expect(response.body).toMatchObject({
      orderId,
      orderNumber: 'LUM-260405-ABC123',
      status: 'paid',
    });
  });
});
