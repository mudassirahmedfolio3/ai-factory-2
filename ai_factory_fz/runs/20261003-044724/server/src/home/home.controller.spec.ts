import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ErrorResponseFilter } from '../common/error-response.filter.js';
import { HomeController } from './home.controller.js';
import { HomeService } from './home.service.js';

describe('HomeController (Supertest)', () => {
  let app: INestApplication<App>;
  const homeService = { getHome: vi.fn() };

  beforeEach(async () => {
    vi.resetAllMocks();
    const moduleFixture: TestingModule = await Test.createTestingModule({
      controllers: [HomeController],
      providers: [{ provide: HomeService, useValue: homeService }],
    }).compile();

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

  it('GET /api/v1/home returns merchandised home payload', async () => {
    homeService.getHome.mockResolvedValue({
      banners: [],
      featured: [],
      newArrivals: [],
      categories: [],
    });

    const res = await request(app.getHttpServer()).get('/api/v1/home');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      banners: [],
      featured: [],
      newArrivals: [],
      categories: [],
    });
    expect(homeService.getHome).toHaveBeenCalledOnce();
  });
});
