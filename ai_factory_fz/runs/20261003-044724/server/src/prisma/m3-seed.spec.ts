import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

describe('M3 prisma seed (WI-010)', () => {
  const seedSource = readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), '../../prisma/seed.ts'),
    'utf8',
  );

  it('seeds StoreConfig shipping and tax defaults', () => {
    expect(seedSource).toContain('freeShippingThresholdCents: 7500');
    expect(seedSource).toContain('flatShippingCents: 599');
    expect(seedSource).toContain('taxRateBps: 800');
  });

  it('seeds coupons with exclusions and demo fulfillment orders', () => {
    expect(seedSource).toContain("code: 'WELCOME10'");
    expect(seedSource).toContain('CouponExclusionKind');
    expect(seedSource).toContain('carrierName:');
    expect(seedSource).toContain('trackingNumber:');
    expect(seedSource).toContain("orderNumber: 'SE-20261004-SHIP01'");
  });

  it('seeds home banners for merchandised home', () => {
    expect(seedSource).toContain('homeBanner.create');
    expect(seedSource).toContain('banner-spring-home');
  });

  it('seeds US-004 launch categories (BUG-001)', () => {
    expect(seedSource).toContain("name: 'Clothing'");
    expect(seedSource).toContain("name: 'Electronics'");
    expect(seedSource).toContain("name: 'Home & Kitchen'");
    expect(seedSource).toContain("name: 'Beauty'");
    expect(seedSource).toContain("name: 'Sports & Outdoors'");
  });

  it('seeds 50+ catalog products for filter demos (BUG-002)', () => {
    expect(seedSource).toContain('buildExpandedCatalog');
    const coreProducts =
      seedSource.match(/^\s+key: 'seed-product-\d+',$/gm)?.length ?? 0;
    const expandedBlock = seedSource.slice(
      seedSource.indexOf('EXPANDED_CATALOG_NAMES'),
      seedSource.indexOf('function stockQuantityForDemoIndex'),
    );
    const expandedNames = expandedBlock.match(/^\s+'[^']+',$/gm)?.length ?? 0;
    expect(coreProducts + expandedNames).toBeGreaterThanOrEqual(50);
  });
});
