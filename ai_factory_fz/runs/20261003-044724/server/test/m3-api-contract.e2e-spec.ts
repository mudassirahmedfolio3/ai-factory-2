/**
 * WI-020: HTTP contract regression for M3 catalog/home endpoints against a
 * migrated + seeded Postgres (skipped locally when E2E_DATABASE_AVAILABLE=0).
 */
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eAppWithRealPrisma,
  isE2eDatabaseAvailable,
} from './e2e-app.factory.js';

const db = isE2eDatabaseAvailable();

describe.skipIf(!db)('M3 API contract (seeded Postgres, WI-020)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    app = await createE2eAppWithRealPrisma();
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /api/v1/health returns 200 with { status: "ok", database: "reachable" }', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health');
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ status: 'ok', database: 'up' });
    expect(res.body.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('GET /api/v1/categories returns CategoryListResponse shape', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/categories');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.items)).toBe(true);
    for (const category of res.body.items) {
      expect(category).toMatchObject({
        id: expect.any(String),
        slug: expect.any(String),
        name: expect.any(String),
      });
    }
  });

  it('GET /api/v1/products returns flat pagination fields per OpenAPI', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/products');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.items)).toBe(true);
    expect(res.body).toMatchObject({
      total: expect.any(Number),
      page: expect.any(Number),
      pageSize: expect.any(Number),
    });
  });

  it('GET /api/v1/products with pageSize over 100 returns contract-shaped 400', async () => {
    const res = await request(app.getHttpServer()).get(
      '/api/v1/products?pageSize=101',
    );
    expect(res.status).toBe(400);
    expect(res.body).toMatchObject({
      statusCode: 400,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('GET /api/v1/products/{productId} returns ProductDetail for a seeded product', async () => {
    const list = await request(app.getHttpServer()).get(
      '/api/v1/products?page=1&pageSize=1',
    );
    const productId = list.body.items[0].id as string;

    const res = await request(app.getHttpServer()).get(
      `/api/v1/products/${productId}`,
    );
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      id: productId,
      name: expect.any(String),
      brand: expect.any(String),
      description: expect.any(String),
      primaryImageUrl: expect.any(String),
      availability: expect.any(String),
    });
    expect(res.body.category).toMatchObject({
      id: expect.any(String),
      slug: expect.any(String),
      name: expect.any(String),
    });
    expect(Array.isArray(res.body.variants)).toBe(true);
  });

  it('GET /api/v1/home returns merchandised home payload', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/home');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.banners)).toBe(true);
    expect(Array.isArray(res.body.featured)).toBe(true);
    expect(Array.isArray(res.body.newArrivals)).toBe(true);
    expect(Array.isArray(res.body.categories)).toBe(true);
  });
});

describe('M3 API contract (database unavailable)', () => {
  it.skipIf(db)(
    'skipped: start Postgres (see repo docker-compose.yml) for seeded HTTP contract tests',
    () => {
      expect(isE2eDatabaseAvailable()).toBe(false);
    },
  );
});
