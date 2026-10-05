// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
// Plain HTTP smoke test against SMOKE_BASE_URL; imports no application code.
const base = process.env.SMOKE_BASE_URL ?? 'http://localhost:3000';
// Unique test data per run.
const deviceId = `smoke-${Date.now()}-${Math.random().toString(16).slice(2)}`;

async function call(method: string, path: string, token?: string, body?: unknown) {
  const res = await fetch(base + path, {
    method,
    headers: { 'content-type': 'application/json', ...(token ? { authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: res.status, json: await res.json().catch(() => null) };
}

function expect(cond: boolean, message: string) {
  if (!cond) throw new Error(`SMOKE FAIL: ${message}`);
}

async function main() {
  const health = await call('GET', '/health');
  expect(health.status === 200, `GET /health expected 200, got ${health.status}`);

  const session = await call('POST', '/auth/anonymous', undefined, { deviceId });
  expect(session.status === 200 && !!session.json?.token, 'anonymous sign-in should return a token');
  const token = session.json.token;

  const list = await call('GET', '/products', token);
  expect(list.status === 200 && list.json.items.length > 0, 'browse: product list should not be empty');
  const productId = list.json.items[0].id;

  const detail = await call('GET', `/products/${productId}`, token);
  expect(detail.status === 200 && detail.json.id === productId, 'product detail should return the product');

  await call('POST', '/cart/items', token, { productId });
  const cart = await call('POST', '/cart/items', token, { productId });
  expect(cart.json.items[0].quantity === 2, `adding twice should give quantity 2, got ${cart.json.items[0].quantity}`);
  expect(cart.json.totalCents === 2 * detail.json.priceCents, 'cart total should equal 2 x unit price');
  console.log('smoke ok');
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
