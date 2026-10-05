import {
  BadRequestException,
  INestApplication,
  ValidationPipe,
} from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { JwtModule } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard.js';
import { ErrorResponseFilter } from '../common/error-response.filter.js';
import { CartController } from './cart.controller.js';
import { CartService } from './cart.service.js';

describe('CartController (Supertest)', () => {
  let app: INestApplication<App>;
  const cartService = {
    getCart: vi.fn(),
    replaceCart: vi.fn(),
    mergeCart: vi.fn(),
  };

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
      controllers: [CartController],
      providers: [{ provide: CartService, useValue: cartService }],
    })
      .overrideGuard(JwtAuthGuard)
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
        exceptionFactory: (errors) => {
          const firstConstraint = errors[0]?.constraints;
          const firstMessage =
            firstConstraint === undefined
              ? 'Validation failed'
              : Object.values(firstConstraint)[0];
          return new BadRequestException(firstMessage);
        },
      }),
    );
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /api/v1/cart returns cart payload', async () => {
    cartService.getCart.mockResolvedValue({
      items: [],
      subtotal: { amountCents: 0, currency: 'USD' },
    });

    const res = await request(app.getHttpServer()).get('/api/v1/cart');

    expect(res.status).toBe(200);
    expect(cartService.getCart).toHaveBeenCalledWith('user-1');
  });

  it('POST /api/v1/cart/merge forwards guest items', async () => {
    cartService.mergeCart.mockResolvedValue({
      items: [],
      subtotal: { amountCents: 0, currency: 'USD' },
    });

    const res = await request(app.getHttpServer())
      .post('/api/v1/cart/merge')
      .send({
        guestItems: [{ variantId: '550e8400-e29b-41d4-a716-446655440000', quantity: 1 }],
      });

    expect(res.status).toBe(200);
    expect(cartService.mergeCart).toHaveBeenCalledWith(
      'user-1',
      [{ variantId: '550e8400-e29b-41d4-a716-446655440000', quantity: 1 }],
      'merge',
    );
  });
});
