import assert from 'node:assert/strict';
import test from 'node:test';
import { validateGetHealthBody, probeGetHealth } from './health-smoke.mjs';

test('validateGetHealthBody accepts contract-shaped 200 payload', () => {
  const result = validateGetHealthBody({
    status: 'ok',
    database: 'up',
    timestamp: '2026-10-04T12:00:00.000Z',
  });
  assert.equal(result.ok, true);
});

test('validateGetHealthBody rejects degraded or down database', () => {
  assert.equal(
    validateGetHealthBody({ status: 'degraded', database: 'up', timestamp: '2026-10-04T12:00:00.000Z' })
      .ok,
    false,
  );
  assert.equal(
    validateGetHealthBody({ status: 'ok', database: 'down', timestamp: '2026-10-04T12:00:00.000Z' })
      .ok,
    false,
  );
});

test('probeGetHealth maps HTTP status and JSON', async () => {
  const mockFetch = async () =>
    new Response(JSON.stringify({ status: 'ok', database: 'up', timestamp: '2026-10-04T12:00:00.000Z' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  const result = await probeGetHealth('http://127.0.0.1:3000/health', { fetchFn: mockFetch });
  assert.equal(result.ok, true);
  assert.equal(result.status, 200);
});
