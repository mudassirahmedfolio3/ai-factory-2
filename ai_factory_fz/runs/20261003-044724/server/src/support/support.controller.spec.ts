import { INestApplication, ValidationPipe } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { JwtModule } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OptionalJwtAuthGuard } from '../auth/guards/optional-jwt-auth.guard.js';
import { ErrorResponseFilter } from '../common/error-response.filter.js';
import { SupportController } from './support.controller.js';
import { SupportService } from './support.service.js';

describe('SupportController (Supertest)', () => {
  let app: INestApplication<App>;
  const supportService = { submitMessage: vi.fn() };

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
      controllers: [SupportController],
      providers: [{ provide: SupportService, useValue: supportService }],
    })
      .overrideGuard(OptionalJwtAuthGuard)
      .useValue({ canActivate: () => true })
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

  it('POST /api/v1/support/messages returns 201', async () => {
    supportService.submitMessage.mockResolvedValue({
      id: 'msg-1',
      message: 'Thanks',
    });

    await request(app.getHttpServer())
      .post('/api/v1/support/messages')
      .send({
        email: 'shopper@example.com',
        subject: 'Help',
        body: 'Need assistance with my order',
      })
      .expect(201);
  });
});
