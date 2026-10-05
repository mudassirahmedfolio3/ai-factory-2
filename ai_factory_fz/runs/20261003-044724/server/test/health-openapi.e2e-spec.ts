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

describe('Health + OpenAPI contract (WI-006 / WI-020)', () => {
  describe('Swagger (no database)', () => {
    let app: INestApplication<App>;

    beforeEach(async () => {
      app = await createE2eApp();
    });

    afterEach(async () => {
      await app.close();
    });

    it('GET /api/docs-json exposes getHealth at /health and documents a 503 response', async () => {
      const res = await request(app.getHttpServer()).get('/api/docs-json');
      expect(res.status).toBe(200);
      expect(res.body.paths['/health'].get.operationId).toBe('getHealth');
      expect(res.body.paths['/health'].get.responses).toHaveProperty('200');
      expect(res.body.paths['/health'].get.responses).toHaveProperty('503');
    });
  });

  describe.skipIf(!db)('Health probe (seeded Postgres)', () => {
    let app: INestApplication<App>;

    beforeEach(async () => {
      app = await createE2eAppWithRealPrisma();
    });

    afterEach(async () => {
      await app.close();
    });

    it('GET /api/v1/health returns the health payload when the database is reachable', async () => {
      const res = await request(app.getHttpServer()).get('/api/v1/health');
      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({ status: 'ok', database: 'up' });
      expect(res.body.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('GET /health returns the unprefixed infrastructure health payload', async () => {
      const res = await request(app.getHttpServer()).get('/health');
      expect(res.status).toBe(200);
      expect(res.body).toMatchObject({ status: 'ok', database: 'up' });
      expect(res.body.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });
  });
});
