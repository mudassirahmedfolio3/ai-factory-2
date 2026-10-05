import { Decimal } from '@prisma/client/runtime/library';
import { join } from 'path';
import {
  assertM3CatalogParity,
  brandIdBySlug,
  computeAverageRating,
  loadCatalogDocument,
  resolveCatalogJsonPath,
  variantReservedQuantity,
} from './catalog-seed.loader';
import { M3_CATALOG_PARITY } from './catalog-seed.constants';

describe('catalog-seed.loader', () => {
  const catalogPath = join(process.cwd(), 'prisma/data/catalog.json');

  it('resolves bundled catalog.json under prisma/data', () => {
    expect(resolveCatalogJsonPath()).toBe(catalogPath);
  });

  it('loads M3 catalog document matching parity counts', () => {
    const document = loadCatalogDocument(catalogPath);
    expect(() => assertM3CatalogParity(document)).not.toThrow();
    expect(document.brands).toHaveLength(M3_CATALOG_PARITY.brandCount);
    expect(document.products).toHaveLength(M3_CATALOG_PARITY.productCount);
    expect(document.coupons).toHaveLength(M3_CATALOG_PARITY.couponCount);
  });

  it('computes average rating to two decimal places', () => {
    const average = computeAverageRating([
      {
        id: 'r1',
        rating: 4,
        title: 't',
        body: 'b',
        authorDisplayName: 'a',
        createdAt: '2026-01-01T00:00:00.000Z',
      },
      {
        id: 'r2',
        rating: 5,
        title: 't',
        body: 'b',
        authorDisplayName: 'a',
        createdAt: '2026-01-01T00:00:00.000Z',
      },
    ]);
    expect(average).toEqual(new Decimal('4.50'));
  });

  it('derives reserved quantity from stock minus available', () => {
    expect(variantReservedQuantity(10, 7)).toBe(3);
    expect(variantReservedQuantity(5, 8)).toBe(0);
  });

  it('maps brand slug to stable UUID from seed', () => {
    const document = loadCatalogDocument(catalogPath);
    expect(brandIdBySlug(document, 'luminex')).toBe(
      'b1111111-1111-4111-8111-111111111101',
    );
  });
});
