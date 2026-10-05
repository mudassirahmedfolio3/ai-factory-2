import { INestApplication, ValidationPipe } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ErrorResponseFilter } from '../common/error-response.filter.js';
import { CatalogController } from './catalog.controller.js';
import { CatalogService } from './catalog.service.js';

describe('CatalogController (Supertest)', () => {
  let app: INestApplication<App>;
  const catalogService = {
    listCategories: vi.fn(),
    listProducts: vi.fn(),
    getProductById: vi.fn(),
  };

  beforeEach(async () => {
    vi.resetAllMocks();
    const moduleFixture: TestingModule = await Test.createTestingModule({
      controllers: [CatalogController],
      providers: [{ provide: CatalogService, useValue: catalogService }],
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

  it('GET /api/v1/products rejects undocumented query params', async () => {
    const res = await request(app.getHttpServer()).get(
      '/api/v1/products?unknownParam=1',
    );

    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({
      statusCode: 400,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('GET /api/v1/products passes q and sort to the service', async () => {
    catalogService.listProducts.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
    });

    const res = await request(app.getHttpServer()).get(
      '/api/v1/products?q=soap&sort=priceAsc',
    );

    expect(res.status).toBe(200);
    expect(catalogService.listProducts).toHaveBeenCalledWith(
      expect.objectContaining({ q: 'soap', sort: 'priceAsc' }),
    );
  });
});
