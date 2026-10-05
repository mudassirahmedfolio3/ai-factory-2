import { beforeEach, describe, expect, it, vi } from 'vitest';
import { WishlistService } from './wishlist.service.js';

describe('WishlistService', () => {
  const prisma = {
    wishlist: {
      upsert: vi.fn(),
    },
    wishlistItem: {
      findMany: vi.fn(),
      deleteMany: vi.fn(),
      createMany: vi.fn(),
    },
    product: {
      findMany: vi.fn(),
    },
    $transaction: vi.fn(),
  };

  let service: WishlistService;

  beforeEach(() => {
    vi.resetAllMocks();
    prisma.$transaction.mockImplementation(
      async (fn: (tx: typeof prisma) => Promise<unknown>) => fn(prisma),
    );
    prisma.wishlist.upsert.mockResolvedValue({ id: 'wish-1' });
    service = new WishlistService(prisma as never);
  });

  it('importWishlist adds only new active products', async () => {
    prisma.product.findMany.mockResolvedValue([
      { id: 'prod-1' },
      { id: 'prod-2' },
    ]);
    prisma.wishlistItem.findMany
      .mockResolvedValueOnce([{ productId: 'prod-1' }])
      .mockResolvedValueOnce([
      {
        productId: 'prod-1',
        createdAt: new Date('2026-01-01T00:00:00.000Z'),
      },
      {
        productId: 'prod-2',
        createdAt: new Date('2026-01-02T00:00:00.000Z'),
      },
    ]);

    const result = await service.importWishlist('user-1', [
      'prod-1',
      'prod-2',
      'missing-prod',
    ]);

    expect(prisma.wishlistItem.createMany).toHaveBeenCalledWith({
      data: [{ wishlistId: 'wish-1', productId: 'prod-2' }],
      skipDuplicates: true,
    });
    expect(result.items).toHaveLength(2);
  });

  it('replaceWishlist dedupes product IDs', async () => {
    prisma.product.findMany.mockResolvedValue([{ id: 'prod-1' }]);
    prisma.wishlistItem.findMany.mockResolvedValue([
      {
        productId: 'prod-1',
        createdAt: new Date('2026-01-01T00:00:00.000Z'),
      },
    ]);

    await service.replaceWishlist('user-1', ['prod-1', 'prod-1']);

    expect(prisma.wishlistItem.createMany).toHaveBeenCalledWith({
      data: [{ wishlistId: 'wish-1', productId: 'prod-1' }],
    });
  });
});
