import {
  INestApplication,
  UnauthorizedException,
  ValidationPipe,
} from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { JwtModule } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OptionalJwtAuthGuard } from '../auth/guards/optional-jwt-auth.guard.js';
import { ErrorResponseFilter } from '../common/error-response.filter.js';
import { CheckoutController } from './checkout.controller.js';
import { CheckoutService } from './checkout.service.js';

describe('CheckoutController (Supertest)', () => {
  let app: INestApplication<App>;
  const checkoutService = { createQuote: vi.fn() };

  beforeEach(async () => {
    vi.resetAllMocks();
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          isGlobal: true,
          load: [() => ({ JWT_SECRET: 'test-secret' })],
        }),
        JwtModule.register({ secret: 'test-secret' }),
      ],
      controllers: [CheckoutController],
      providers: [{ provide: CheckoutService, useValue: checkoutService }],
    })
      .overrideGuard(OptionalJwtAuthGuard)
      .useValue({
        canActivate: (context: {
          switchToHttp: () => {
            getRequest: () => { user?: { id: string } };
          };
        }) => {
          const req = context.switchToHttp().getRequest();
          req.user = { id: 'user-1' };
          return true;
        },
      })
      .compile();

    app = moduleFixture.createNestApplication();
    app.setGlobalPrefix('api/v1');
    app.useGlobalFilters(new ErrorResponseFilter());
    app.useGlobalPipes(
      new ValidationPipe({
        transform: true,
        whitelist: true,
        forbidNonWhitelisted: true,
      }),
    );
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('POST /api/v1/checkout/quote returns quote', async () => {
    checkoutService.createQuote.mockResolvedValue({
      lines: [],
      subtotal: { amountCents: 0, currency: 'USD' },
      discount: { amountCents: 0, currency: 'USD' },
      shipping: { amountCents: 0, currency: 'USD' },
      tax: { amountCents: 0, currency: 'USD' },
      total: { amountCents: 0, currency: 'USD' },
      coupon: { valid: false },
    });

    await request(app.getHttpServer())
      .post('/api/v1/checkout/quote')
      .send({
        shippingAddress: {
          fullName: 'Jane',
          line1: '1 Main',
          city: 'Austin',
          region: 'TX',
          postalCode: '78701',
          country: 'US',
        },
      })
      .expect(200);

    expect(checkoutService.createQuote).toHaveBeenCalled();
  });

  it('maps unauthorized to 401', async () => {
    checkoutService.createQuote.mockRejectedValue(new UnauthorizedException());

    const res = await request(app.getHttpServer())
      .post('/api/v1/checkout/quote')
      .send({
        shippingAddress: {
          fullName: 'Jane',
          line1: '1 Main',
          city: 'Austin',
          region: 'TX',
          postalCode: '78701',
          country: 'US',
        },
      })
      .expect(401);

    expect(res.body.statusCode).toBe(401);
  });
});
