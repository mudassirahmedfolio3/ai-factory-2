#!/usr/bin/env node
/**
 * M3 staging smoke: health liveness, OpenAPI parity (28 counted ops + getHealth),
 * and catalog merchandising against a seeded DB.
 * Run after `docker compose up --build` or staging compose with secrets exported.
 */
import {
  M3_CATALOG_PARITY,
  M3_COUNTED_OPERATION_IDS,
  M3_HEALTH_OPERATION_ID,
} from './m3-smoke-constants.mjs';

const baseUrl = (process.env.API_BASE_URL ?? 'http://localhost:3000').replace(
  /\/$/,
  '',
);
const apiPrefix = `${baseUrl}/api/v1`;
const spotProductId =
  process.env.SMOKE_PRODUCT_ID ?? 'p1111111-1111-4111-8111-111111111101';

const checks = [];

async function getJson(path, label, init) {
  const url = `${apiPrefix}${path}`;
  const response = await fetch(url, init);
  const body = await response.json().catch(() => ({}));
  checks.push({ label, ok: response.ok, status: response.status, url });
  if (!response.ok) {
    throw new Error(`${label} failed (${response.status}) ${url}`);
  }
  return body;
}

function collectOperationIds(openApi) {
  const ids = new Set();
  for (const pathItem of Object.values(openApi.paths ?? {})) {
    for (const operation of Object.values(pathItem ?? {})) {
      if (operation?.operationId) {
        ids.add(operation.operationId);
      }
    }
  }
  return ids;
}

async function main() {
  const health = await getJson('/health', M3_HEALTH_OPERATION_ID);
  if (health.status !== 'ok' || health.database !== 'up') {
    throw new Error(
      `${M3_HEALTH_OPERATION_ID}: expected status ok and database up`,
    );
  }

  const openApiResponse = await fetch(`${baseUrl}/api/docs-json`);
  if (!openApiResponse.ok) {
    throw new Error(`OpenAPI publication failed (${openApiResponse.status})`);
  }
  const openApi = await openApiResponse.json();
  const publishedIds = collectOperationIds(openApi);

  for (const operationId of [
    M3_HEALTH_OPERATION_ID,
    ...M3_COUNTED_OPERATION_IDS,
  ]) {
    if (!publishedIds.has(operationId)) {
      throw new Error(`OpenAPI missing operationId ${operationId}`);
    }
  }
  if (M3_COUNTED_OPERATION_IDS.length !== 28) {
    throw new Error('M3 smoke constants: expected exactly 28 counted operations');
  }

  const home = await getJson('/home', 'getHome');
  if (
    !Array.isArray(home.categories) ||
    home.categories.length < M3_CATALOG_PARITY.minCategoryCount
  ) {
    throw new Error(
      `getHome: expected at least ${M3_CATALOG_PARITY.minCategoryCount} categories (is DB seeded?)`,
    );
  }
  if (!Array.isArray(home.featuredProducts) || home.featuredProducts.length < 1) {
    throw new Error('getHome: expected featured products');
  }
  if (!Array.isArray(home.banners) || home.banners.length < 1) {
    throw new Error('getHome: expected home banners (M3 merchandising)');
  }

  await getJson('/categories?depth=1', 'listCategories');
  await getJson('/categories/ceiling-lights', 'getCategoryBySlug');
  await getJson('/catalog/facets', 'getCatalogFacets');

  const products = await getJson(
    '/products?page=1&pageSize=100',
    'listProducts',
  );
  if (
    typeof products.total !== 'number' ||
    products.total < M3_CATALOG_PARITY.minProductCount
  ) {
    throw new Error(
      `listProducts: expected total >= ${M3_CATALOG_PARITY.minProductCount} seeded SKUs, got ${products.total}`,
    );
  }
  const first = products.items?.[0];
  if (
    first?.price?.currency !== 'GBP' ||
    typeof first?.price?.amountCents !== 'number'
  ) {
    throw new Error('listProducts: expected GBP integer amountCents on items');
  }

  await getJson(`/products/${spotProductId}`, 'getProductById');
  await getJson(
    `/products/${spotProductId}/reviews?page=1&pageSize=5`,
    'listProductReviews',
  );

  console.log(
    JSON.stringify(
      {
        ok: true,
        baseUrl,
        openApiVersion: openApi.info?.version,
        countedOperations: M3_COUNTED_OPERATION_IDS.length,
        checks: checks.map(({ label, status }) => ({ label, status })),
        productTotal: products.total,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.message ?? error);
  process.exit(1);
});
