/**
 * QA regression suite for Milestone M2 (Backend Catalog OpenAPI Slice & Integration).
 *
 * Assertions derived from docs/openapi.yaml and US-006 AC1. Bootstrap uses
 * setupApplication so the global /api/v1 prefix, ValidationPipe, Swagger, and
 * unprefixed /health probe match production.
 *
 * M3 operation-count caps are covered in m3-openapi-surface.e2e-spec.ts.
 */
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eApp,
  createE2eAppWithRealPrisma,
  isE2eDatabaseAvailable,
} from './e2e-app.factory.js';

const db = isE2eDatabaseAvailable();

describe('M2 contract (docs/openapi.yaml + infra endpoints, no DB)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    app = await createE2eApp();
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /health (unprefixed infra probe) returns 200', async () => {
    const res = await request(app.getHttpServer()).get('/health');
    expect(res.status).toBe(200);
  });

  it('GET /api/docs-json exposes the OpenAPI document (outside the /api/v1 prefix)', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('paths');
  });

  it('GET /api/docs-json declares server URLs with the /api/v1 prefix', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.status).toBe(200);
    expect(res.body.servers).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ url: 'http://10.0.2.2:3000/api/v1' }),
        expect.objectContaining({
          url: 'https://api.staging.shopease.example/api/v1',
        }),
      ]),
    );
  });

  it('GET /api/docs-json exposes catalog/health operations with contract operationIds', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.status).toBe(200);

    const paths = res.body.paths as Record<
      string,
      Record<string, { operationId?: string }>
    >;
    expect(paths['/health'].get?.operationId).toBe('getHealth');
    expect(paths['/categories'].get?.operationId).toBe('listCategories');
    expect(paths['/products'].get?.operationId).toBe('listProducts');
    expect(paths['/products/{productId}'].get?.operationId).toBe(
      'getProductById',
    );

    expect(paths['/api/v1/health']).toBeUndefined();
  });

  it('GET /api/docs-json includes the documented 503 response for GET /health', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.status).toBe(200);
    expect(res.body.paths['/health'].get.responses).toHaveProperty('503');
  });
});

describe.skipIf(!db)(
  'M2 contract (catalog HTTP + health against seeded Postgres)',
  () => {
    let app: INestApplication<App>;

    beforeEach(async () => {
      app = await createE2eAppWithRealPrisma();
    });

    afterEach(async () => {
      await app.close();
    });

    it('GET /api/v1/health returns 200 with { status: "ok", database: "reachable" } per openapi.yaml', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/health');
      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({ status: 'ok', database: 'reachable' });
    });

    it('GET /api/v1/categories returns 200 with a CategoryListResponse shape', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/categories');
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.items)).toBe(true);
    });

    it('GET /api/v1/products returns 200 with a paginated ProductListResponse shape', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/products');
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.items)).toBe(true);
      expect(res.body).toMatchObject({
        page: expect.any(Number),
        pageSize: expect.any(Number),
        total: expect.any(Number),
      });
    });

    it('GET /api/v1/products/{productId} for an unknown id returns a contract-shaped 404', async () => {
      const res = await request(app.getHttpServer()).get(
        '/api/v1/products/00000000-0000-0000-0000-000000000000',
      );
      expect(res.status).toBe(404);
      expect(res.body).toMatchObject({
        statusCode: 404,
        error: expect.any(String),
        message: expect.any(String),
      });
    });

    it('GET /api/v1/products with an invalid priceBand returns a contract-shaped 400', async () => {
      const res = await request(app.getHttpServer()).get(
        '/api/v1/products?priceBand=luxury',
      );
      expect(res.status).toBe(400);
      expect(res.body).toMatchObject({
        statusCode: 400,
        error: expect.any(String),
        message: expect.any(String),
      });
    });

    it('GET /api/v1/products with pageSize over the max returns a contract-shaped 400', async () => {
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

    it('GET /api/v1/products with an undocumented query param returns a contract-shaped 400', async () => {
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

    it('GET /api/v1/products/{productId} with a malformed id returns 400, not 500', async () => {
      const res = await request(app.getHttpServer()).get(
        '/api/v1/products/not-a-uuid',
      );
      expect(res.status).toBe(400);
    });

    it('GET /api/v1/categories items match the Category schema shape', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/categories');
      expect(res.status).toBe(200);
      for (const category of res.body.items) {
        expect(category).toMatchObject({
          id: expect.any(String),
          slug: expect.any(String),
          name: expect.any(String),
        });
      }
    });

    it('GET /api/v1/products paginates and reports total across pages', async () => {
      const pageOne = await request(app.getHttpServer()).get(
        '/api/v1/products?page=1&pageSize=1',
      );
      expect(pageOne.status).toBe(200);
      expect(pageOne.body.items.length).toBeLessThanOrEqual(1);
      expect(pageOne.body).toMatchObject({ page: 1, pageSize: 1 });
    });

    it('GET /api/v1/products/{productId} for a seeded product returns a contract-shaped ProductDetail', async () => {
      const list = await request(app.getHttpServer()).get(
        '/api/v1/products?page=1&pageSize=1',
      );
      expect(list.status).toBe(200);
      expect(list.body.items.length).toBe(1);
      const productId = list.body.items[0].id as string;

      const res = await request(app.getHttpServer()).get(
        `/api/v1/products/${productId}`,
      );

      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({
        id: productId,
        name: expect.any(String),
        description: expect.any(String),
        categorySlug: expect.any(String),
        isAvailable: expect.any(Boolean),
        averageRating: expect.any(Number),
        reviewCount: expect.any(Number),
      });
      expect(Array.isArray(res.body.images)).toBe(true);
      expect(Array.isArray(res.body.variants)).toBe(true);
      for (const variant of res.body.variants) {
        expect(variant).toMatchObject({
          id: expect.any(String),
          sku: expect.any(String),
          name: expect.any(String),
          price: {
            amountCents: expect.any(Number),
            currency: expect.any(String),
          },
          inventoryCount: expect.any(Number),
          isAvailable: expect.any(Boolean),
        });
      }
    });

  },
);
