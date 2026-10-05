import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/**
 * M3 / US-004 & US-005: Prisma seed must expose launch categories and a demo
 * catalog large enough for search, sort, and filter acceptance.
 */
const US004_CATEGORY_NAMES = [
  'Clothing',
  'Electronics',
  'Home & Kitchen',
  'Beauty',
  'Sports & Outdoors',
] as const;

const US004_CATEGORY_SLUGS = [
  'clothing',
  'electronics',
  'home-kitchen',
  'beauty',
  'sports-outdoors',
] as const;

function prismaSeedSource(): string {
  const serverRoot = join(dirname(fileURLToPath(import.meta.url)), '../..');
  return readFileSync(join(serverRoot, 'prisma/seed.ts'), 'utf8');
}

describe('Prisma seed launch catalog (US-004 / US-005)', () => {
  const seedSource = prismaSeedSource();

  it('defines US-004 home category entry point names and slugs', () => {
    for (const name of US004_CATEGORY_NAMES) {
      expect(seedSource).toContain(`name: '${name}'`);
    }
    for (const slug of US004_CATEGORY_SLUGS) {
      expect(seedSource).toContain(`slug: '${slug}'`);
    }
    expect(seedSource).not.toContain("slug: 'everyday-essentials'");
    expect(seedSource).not.toContain("slug: 'gift-friendly'");
  });

  it('seeds roughly 50–100 products with multiple variant SKUs', () => {
    const coreProducts =
      seedSource.match(/^\s+key: 'seed-product-\d+',$/gm)?.length ?? 0;
    const expandedBlock = seedSource.slice(
      seedSource.indexOf('EXPANDED_CATALOG_NAMES'),
      seedSource.indexOf('function stockQuantityForDemoIndex'),
    );
    const expandedNames = expandedBlock.match(/^\s+'[^']+',$/gm)?.length ?? 0;
    const totalProducts = coreProducts + expandedNames;
    expect(totalProducts).toBeGreaterThanOrEqual(50);
    expect(totalProducts).toBeLessThanOrEqual(100);
    expect(seedSource).toContain('buildExpandedCatalog');
  });

  it('retains the twelve original demo product keys for order history fixtures', () => {
    for (let n = 1; n <= 12; n += 1) {
      expect(seedSource).toContain(`key: 'seed-product-${n}'`);
    }
  });
});
