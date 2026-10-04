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
import { WishlistController } from './wishlist.controller.js';
import { WishlistService } from './wishlist.service.js';

describe('WishlistController (Supertest)', () => {
  let app: INestApplication<App>;
  const wishlistService = {
    getWishlist: vi.fn(),
    replaceWishlist: vi.fn(),
    importWishlist: vi.fn(),
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
      controllers: [WishlistController],
      providers: [{ provide: WishlistService, useValue: wishlistService }],
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

  it('POST /api/v1/wishlist/import forwards product IDs', async () => {
    wishlistService.importWishlist.mockResolvedValue({ items: [] });

    const res = await request(app.getHttpServer())
      .post('/api/v1/wishlist/import')
      .send({
        productIds: ['550e8400-e29b-41d4-a716-446655440000'],
      });

    expect(res.status).toBe(200);
    expect(wishlistService.importWishlist).toHaveBeenCalledWith('user-1', [
      '550e8400-e29b-41d4-a716-446655440000',
    ]);
  });
});
