/**
 * Contract: unexpected errors and unreachable DB still return { statusCode, error, message }.
 */
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eApp,
  unreachableDatabasePrismaStub,
} from './e2e-app.factory.js';

describe('M2/M3 contract: error response shape (BUG-001 / WI-020)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    const failingPrisma = {
      ...unreachableDatabasePrismaStub(),
      category: {
        findMany: () =>
          Promise.reject(new Error('connection terminated unexpectedly')),
      },
      product: {
        findMany: () =>
          Promise.reject(new Error('connection terminated unexpectedly')),
        count: () =>
          Promise.reject(new Error('connection terminated unexpectedly')),
        findUnique: () =>
          Promise.reject(new Error('connection terminated unexpectedly')),
      },
      $transaction: (ops: Promise<unknown>[]) => Promise.all(ops),
    };

    app = await createE2eApp({ prisma: failingPrisma as never });
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /api/v1/categories: an unexpected Prisma error must still produce { statusCode, error, message }', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/categories');
    expect(res.status).toBe(500);
    expect(res.body).toMatchObject({
      statusCode: 500,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('GET /api/v1/products: an unexpected Prisma error must still produce { statusCode, error, message }', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/products');
    expect(res.status).toBe(500);
    expect(res.body).toMatchObject({
      statusCode: 500,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('GET /api/v1/products/{productId}: an unexpected Prisma error must still produce { statusCode, error, message }', async () => {
    const res = await request(app.getHttpServer()).get(
      '/api/v1/products/00000000-0000-0000-0000-000000000000',
    );
    expect(res.status).toBe(500);
    expect(res.body).toMatchObject({
      statusCode: 500,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('GET /api/v1/health: an unreachable database returns a contract-shaped 503 per openapi.yaml', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health');
    expect(res.status).toBe(503);
    expect(res.body).toMatchObject({
      statusCode: 503,
      error: 'Service Unavailable',
      message: expect.any(String),
    });
  });

  it('GET /health (unprefixed infra probe): an unreachable database also returns a contract-shaped 503', async () => {
    const res = await request(app.getHttpServer()).get('/health');
    expect(res.status).toBe(503);
    expect(res.body).toMatchObject({
      statusCode: 503,
      error: 'Service Unavailable',
      message: expect.any(String),
    });
  });
});
