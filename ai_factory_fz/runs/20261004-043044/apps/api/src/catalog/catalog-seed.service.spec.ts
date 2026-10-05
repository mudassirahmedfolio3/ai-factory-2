jest.mock('@nestjs/common', () => ({
  Injectable: () => (target: unknown) => target,
}));

import { CatalogSeedService } from './catalog-seed.service';
import { loadCatalogDocument } from './catalog-seed.loader';
import { join } from 'path';

describe('CatalogSeedService', () => {
  const catalogPath = join(process.cwd(), 'prisma/data/catalog.json');

  it('loadAndValidateDocument passes M3 parity checks', () => {
    const prisma = {} as never;
    const service = new CatalogSeedService(prisma);
    const document = service.loadAndValidateDocument();
    expect(document.products.length).toBeGreaterThan(0);
  });

  it('seedCatalog runs transactional clear and insert', async () => {
    const catalog = loadCatalogDocument(catalogPath);
    const tx = {
      couponRedemption: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      couponCategory: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      couponProduct: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      coupon: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
        create: jest.fn().mockResolvedValue(undefined),
      },
      homeBanner: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
        create: jest.fn().mockResolvedValue(undefined),
      },
      review: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      productImage: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      lightingSpecification: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
      },
      productVariant: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      productViewEvent: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      wishlistItem: { deleteMany: jest.fn().mockResolvedValue(undefined) },
      product: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
        create: jest.fn().mockResolvedValue(undefined),
      },
      category: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
        create: jest.fn().mockResolvedValue(undefined),
      },
      brand: {
        deleteMany: jest.fn().mockResolvedValue(undefined),
        create: jest.fn().mockResolvedValue(undefined),
      },
    };

    const prisma = {
      $transaction: jest.fn(async (fn: (client: typeof tx) => Promise<void>) => {
        await fn(tx);
      }),
    };

    const service = new CatalogSeedService(prisma as never);
    await service.seedCatalog(catalog);

    expect(prisma.$transaction).toHaveBeenCalled();
    expect(tx.brand.create).toHaveBeenCalledTimes(catalog.brands.length);
    expect(tx.product.create).toHaveBeenCalledTimes(catalog.products.length);
    expect(tx.homeBanner.create).toHaveBeenCalledTimes(
      catalog.homeBanners?.length ?? 0,
    );
    expect(tx.coupon.create).toHaveBeenCalledTimes(catalog.coupons?.length ?? 0);
  });
});
