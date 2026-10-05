/**
 * WI-020: End-to-end shopper path — auth, cart, checkout quote, order,
 * mock payment, order history status labels, support (requires seeded DB).
 */
import { createHash } from 'node:crypto';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { App } from 'supertest/types.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  createE2eAppWithRealPrisma,
  isE2eDatabaseAvailable,
} from './e2e-app.factory.js';

function seedUuid(key: string): string {
  const hash = createHash('sha256').update(`demo-retail:${key}`).digest('hex');
  return [
    hash.slice(0, 8),
    hash.slice(8, 12),
    `4${hash.slice(13, 16)}`,
    `${((parseInt(hash.slice(16, 18), 16) & 0x3f) | 0x80).toString(16)}${hash.slice(18, 20)}`,
    hash.slice(20, 32),
  ].join('-');
}

const db = isE2eDatabaseAvailable();
const DEMO_EMAIL = 'demo@shopease.test';
const DEMO_PASSWORD = 'DemoPass123!';
const SOAP_VARIANT_ID = seedUuid('seed-product-1-variant-1');

const US_ADDRESS = {
  fullName: 'Flow Tester',
  email: 'flow.tester@example.com',
  line1: '500 Congress Ave',
  city: 'Austin',
  region: 'TX',
  postalCode: '78701',
  country: 'US',
};

describe.skipIf(!db)('M3 shopper commerce flow (WI-020 e2e)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    app = await createE2eAppWithRealPrisma();
  });

  afterEach(async () => {
    await app.close();
  });

  it('demo user order history maps seeded backend statuses to shopperStatus', async () => {
    const login = await request(app.getHttpServer())
      .post('/api/v1/auth/login')
      .send({ email: DEMO_EMAIL, password: DEMO_PASSWORD });
    expect(login.status).toBe(200);
    const token = login.body.accessToken as string;

    const list = await request(app.getHttpServer())
      .get('/api/v1/orders?page=1&pageSize=10')
      .set('Authorization', `Bearer ${token}`);
    expect(list.status).toBe(200);
    expect(list.body.items.length).toBeGreaterThanOrEqual(2);

    const shipped = list.body.items.find(
      (o: { orderNumber: string }) => o.orderNumber === 'SE-20261004-SHIP01',
    );
    expect(shipped?.shopperStatus).toBe('shipped');

    const detail = await request(app.getHttpServer())
      .get(`/api/v1/orders/${shipped.id}`)
      .set('Authorization', `Bearer ${token}`);
    expect(detail.status).toBe(200);
    expect(detail.body).toMatchObject({
      shopperStatus: 'shipped',
      backendStatus: 'fulfilled',
      carrierName: 'UPS',
      trackingNumber: expect.any(String),
    });
  });

  it('registers a shopper, checks out with mock payment, and reads processing status', async () => {
    const email = `wi020-${Date.now()}@example.com`;
    const password = 'Password1';

    const register = await request(app.getHttpServer())
      .post('/api/v1/auth/register')
      .send({ email, password });
    expect(register.status).toBe(201);
    const token = register.body.accessToken as string;

    await request(app.getHttpServer())
      .put('/api/v1/cart')
      .set('Authorization', `Bearer ${token}`)
      .send({
        items: [{ variantId: SOAP_VARIANT_ID, quantity: 1 }],
      })
      .expect(200);

    const quote = await request(app.getHttpServer())
      .post('/api/v1/checkout/quote')
      .set('Authorization', `Bearer ${token}`)
      .send({ shippingAddress: US_ADDRESS, useServerCart: true });
    expect(quote.status).toBe(200);
    expect(quote.body.total.amountCents).toBeGreaterThan(0);

    const orderRes = await request(app.getHttpServer())
      .post('/api/v1/orders')
      .set('Authorization', `Bearer ${token}`)
      .send({
        shippingAddress: US_ADDRESS,
        useServerCart: true,
        idempotencyKey: `wi020-${Date.now()}`,
      });
    expect(orderRes.status).toBe(201);
    expect(orderRes.body.shopperStatus).toBe('awaiting_payment');
    expect(orderRes.body.backendStatus).toBe('pending_payment');

    const paid = await request(app.getHttpServer())
      .post(`/api/v1/orders/${orderRes.body.id}/complete-mock-payment`)
      .set('Authorization', `Bearer ${token}`)
      .send({});
    expect(paid.status).toBe(200);
    expect(paid.body.shopperStatus).toBe('processing');
    expect(paid.body.backendStatus).toBe('paid');
    expect(paid.body.lines[0]).toMatchObject({
      productName: expect.any(String),
      unitPrice: { amountCents: expect.any(Number), currency: 'USD' },
    });

    const support = await request(app.getHttpServer())
      .post('/api/v1/support/messages')
      .set('Authorization', `Bearer ${token}`)
      .send({
        email,
        subject: 'WI-020 test',
        body: 'Automated support message from e2e.',
        orderNumber: orderRes.body.orderNumber,
      });
    expect(support.status).toBe(201);
    expect(support.body.id).toBeTruthy();
  });

  it('rejects listOrders without authentication', async () => {
    const res = await request(app.getHttpServer()).get('/api/v1/orders');
    expect(res.status).toBe(401);
    expect(res.body).toMatchObject({
      statusCode: 401,
      error: expect.any(String),
      message: expect.any(String),
    });
  });

  it('merges guest cart lines after login and manages wishlist import', async () => {
    const email = `wi020-merge-${Date.now()}@example.com`;
    const password = 'Password1';

    const register = await request(app.getHttpServer())
      .post('/api/v1/auth/register')
      .send({ email, password });
    const token = register.body.accessToken as string;

    const list = await request(app.getHttpServer()).get(
      '/api/v1/products?page=1&pageSize=1',
    );
    const productId = list.body.items[0].id as string;

    await request(app.getHttpServer())
      .put('/api/v1/wishlist')
      .set('Authorization', `Bearer ${token}`)
      .send({ productIds: [productId] })
      .expect(200);

    const merge = await request(app.getHttpServer())
      .post('/api/v1/cart/merge')
      .set('Authorization', `Bearer ${token}`)
      .send({
        guestItems: [{ variantId: SOAP_VARIANT_ID, quantity: 2 }],
        strategy: 'merge',
      });
    expect(merge.status).toBe(200);
    expect(merge.body.items.some((i: { variantId: string }) => i.variantId === SOAP_VARIANT_ID)).toBe(
      true,
    );

    const importRes = await request(app.getHttpServer())
      .post('/api/v1/wishlist/import')
      .set('Authorization', `Bearer ${token}`)
      .send({ productIds: [productId] });
    expect(importRes.status).toBe(200);
    expect(importRes.body.items.some((i: { productId: string }) => i.productId === productId)).toBe(
      true,
    );
  });
});
