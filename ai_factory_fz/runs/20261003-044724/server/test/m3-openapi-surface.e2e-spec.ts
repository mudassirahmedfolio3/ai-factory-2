/**
 * WI-020: Live Swagger document must expose the full M3 path/method/operationId
 * surface without requiring Postgres (Prisma stubbed).
 */
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { M3_OPERATION_IDS } from '../src/infra/m3-operation-ids.js';
import { createE2eApp } from './e2e-app.factory.js';

describe('M3 OpenAPI surface (live Swagger, WI-020)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    app = await createE2eApp();
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /api/docs-json exposes every M3 operationId on paths relative to /api/v1', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.status).toBe(200);

    const paths = res.body.paths as Record<
      string,
      Record<string, { operationId?: string }>
    >;

    const liveOperationIds: string[] = [];
    for (const methods of Object.values(paths)) {
      for (const operation of Object.values(methods)) {
        if (operation.operationId) {
          liveOperationIds.push(operation.operationId);
        }
      }
    }
    liveOperationIds.sort();
    expect(liveOperationIds).toEqual([...M3_OPERATION_IDS].sort());
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

  it('counts exactly 24 business operations plus getHealth on /health', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    const paths = res.body.paths as Record<string, Record<string, unknown>>;
    const operationCount = Object.entries(paths).reduce(
      (count, [, methods]) => count + Object.keys(methods).length,
      0,
    );
    expect(operationCount).toBe(M3_OPERATION_IDS.length);
    expect(paths['/health']?.get).toBeDefined();
  });

  it('GET /api/docs-json includes the documented 503 response for GET /health', async () => {
    const res = await request(app.getHttpServer()).get('/api/docs-json');
    expect(res.body.paths['/health'].get.responses).toHaveProperty('503');
  });
});
