import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eAppWithRealPrisma,
  isE2eDatabaseAvailable,
} from './e2e-app.factory.js';

const db = isE2eDatabaseAvailable();

describe.skipIf(!db)('App bootstrap (e2e)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    app = await createE2eAppWithRealPrisma();
  });

  afterEach(async () => {
    await app.close();
  });

  it('GET /api/v1/health is mounted after setupApplication', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok', database: 'reachable' });
  });
});
