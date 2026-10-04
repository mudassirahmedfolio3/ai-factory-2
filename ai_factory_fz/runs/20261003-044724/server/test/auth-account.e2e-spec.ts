import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eAppWithRealPrisma,
  isE2eDatabaseAvailable,
} from './e2e-app.factory.js';

const db = isE2eDatabaseAvailable();

describe.skipIf(!db)('Auth & account self-service (WI-011 / WI-020 e2e)', () => {
  let app: INestApplication<App>;
  const uniqueEmail = () => `wi011-${Date.now()}@example.com`;
  const password = 'Password1';

  beforeEach(async () => {
    app = await createE2eAppWithRealPrisma();
  });

  afterEach(async () => {
    await app.close();
  });

  it('registers, logs in, refreshes, logs out, resets password, and deletes account', async () => {
    const email = uniqueEmail();

    const registerRes = await request(app.getHttpServer())
      .post('/api/v1/auth/register')
      .send({ email, password });
    expect(registerRes.status).toBe(201);
    expect(registerRes.body.accessToken).toBeTruthy();
    expect(registerRes.body.expiresInSeconds).toBe(900);
    expect(registerRes.body.user.email).toBe(email.toLowerCase());
    let accessToken = registerRes.body.accessToken as string;
    let refreshToken = registerRes.body.refreshToken as string;

    const loginRes = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({ email, password });
    expect(loginRes.status).toBe(200);
    refreshToken = loginRes.body.refreshToken;

    const refreshRes = await request(app.getHttpServer())
      .post('/api/v1/auth/refresh')
      .send({ refreshToken });
    expect(refreshRes.status).toBe(200);
    expect(refreshRes.body.accessToken).toBeTruthy();
    accessToken = refreshRes.body.accessToken;
    refreshToken = refreshRes.body.refreshToken;

    const forgotRes = await request(app.getHttpServer())
      .post('/api/v1/auth/forgot-password')
      .send({ email });
    expect(forgotRes.status).toBe(200);
    expect(forgotRes.body.demoResetToken).toBeTruthy();

    const newPassword = 'Newpass99';
    const resetRes = await request(app.getHttpServer())
      .post('/api/v1/auth/reset-password')
      .send({
        email,
        resetToken: forgotRes.body.demoResetToken,
        newPassword,
      });
    expect(resetRes.status).toBe(200);

    const loginNewRes = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({ email, password: newPassword });
    expect(loginNewRes.status).toBe(200);
    accessToken = loginNewRes.body.accessToken;
    refreshToken = loginNewRes.body.refreshToken;

    const logoutRes = await request(app.getHttpServer())
      .post('/api/v1/auth/logout')
      .set('Authorization', `Bearer ${accessToken}`)
      .send({ refreshToken });
    expect(logoutRes.status).toBe(204);

    const deleteRes = await request(app.getHttpServer())
      .delete('/api/v1/users/me')
      .set('Authorization', `Bearer ${accessToken}`);
    expect(deleteRes.status).toBe(204);
  });
});
