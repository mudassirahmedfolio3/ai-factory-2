import { NotFoundException } from '@nestjs/common';
import { Decimal } from '@prisma/client/runtime/library';
import { PrismaService } from '../prisma/prisma.service';
import {
  WISHLIST_ITEM_NOT_FOUND_MESSAGE,
  WISHLIST_PRODUCT_NOT_FOUND_MESSAGE,
} from './wishlist.constants';
import { WishlistService } from './wishlist.service';

const userId = '11111111-1111-4111-8111-111111111111';
const productId = '22222222-2222-4222-8222-222222222222';
const addedAt = new Date('2026-10-04T12:00:00.000Z');

const productWithRelations = {
  id: productId,
  name: 'Modern LED Ceiling Light',
  slug: 'modern-led-ceiling-light',
  primaryImageUrl: 'assets/product.png',
  averageRating: new Decimal('4.5'),
  reviewCount: 12,
  popularityRank: 3,
  isActive: true,
  brand: { name: 'Luminex' },
  category: {
    id: 'c1111111-1111-4111-8111-111111111111',
    name: 'Ceiling',
    slug: 'ceiling-lights',
    parentId: null,
    imageUrl: 'assets/cat.png',
  },
  variants: [
    {
      id: 'v1111111-1111-4111-8111-111111111111',
      sku: 'CL-1001-WH',
      label: 'White',
      priceCents: 4999,
      compareAtCents: null,
      currency: 'GBP',
      stockQuantity: 10,
      reservedQuantity: 0,
      isActive: true,
      isDefault: true,
    },
  ],
};

describe('WishlistService', () => {
  let service: WishlistService;
  let wishlistCount: jest.Mock;
  let wishlistFindMany: jest.Mock;
  let wishlistFindUnique: jest.Mock;
  let wishlistCreate: jest.Mock;
  let wishlistDeleteMany: jest.Mock;
  let productFindFirst: jest.Mock;

  beforeEach(() => {
    wishlistCount = jest.fn();
    wishlistFindMany = jest.fn();
    wishlistFindUnique = jest.fn();
    wishlistCreate = jest.fn();
    wishlistDeleteMany = jest.fn();
    productFindFirst = jest.fn();

    const prisma = {
      wishlistItem: {
        count: wishlistCount,
        findMany: wishlistFindMany,
        findUnique: wishlistFindUnique,
        create: wishlistCreate,
        deleteMany: wishlistDeleteMany,
      },
      product: { findFirst: productFindFirst },
    } as unknown as PrismaService;

    service = new WishlistService(prisma);
  });

  it('listWishlist returns paginated items with product summaries', async () => {
    wishlistCount.mockResolvedValue(1);
    wishlistFindMany.mockResolvedValue([
      {
        productId,
        createdAt: addedAt,
        product: productWithRelations,
      },
    ]);

    const result = await service.listWishlist(userId, { page: 1, pageSize: 20 });

    expect(wishlistFindMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { userId },
        skip: 0,
        take: 20,
      }),
    );
    expect(result.total).toBe(1);
    expect(result.page).toBe(1);
    expect(result.pageSize).toBe(20);
    expect(result.items).toHaveLength(1);
    expect(result.items[0].productId).toBe(productId);
    expect(result.items[0].addedAt).toBe(addedAt.toISOString());
    expect(result.items[0].product.name).toBe('Modern LED Ceiling Light');
  });

  it('addWishlistItem creates a row when product exists', async () => {
    productFindFirst.mockResolvedValue(productWithRelations);
    wishlistFindUnique.mockResolvedValue(null);
    wishlistCreate.mockResolvedValue({
      productId,
      createdAt: addedAt,
      product: productWithRelations,
    });

    const result = await service.addWishlistItem(userId, { productId });

    expect(wishlistCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: { userId, productId },
      }),
    );
    expect(result.productId).toBe(productId);
  });

  it('addWishlistItem is idempotent when item already exists', async () => {
    productFindFirst.mockResolvedValue(productWithRelations);
    wishlistFindUnique.mockResolvedValue({
      productId,
      createdAt: addedAt,
      product: productWithRelations,
    });

    const result = await service.addWishlistItem(userId, { productId });

    expect(wishlistCreate).not.toHaveBeenCalled();
    expect(result.addedAt).toBe(addedAt.toISOString());
  });

  it('addWishlistItem throws 404 when product is missing', async () => {
    productFindFirst.mockResolvedValue(null);

    await expect(
      service.addWishlistItem(userId, { productId }),
    ).rejects.toMatchObject({
      response: { message: WISHLIST_PRODUCT_NOT_FOUND_MESSAGE },
    });
    await expect(
      service.addWishlistItem(userId, { productId }),
    ).rejects.toBeInstanceOf(NotFoundException);
  });

  it('removeWishlistItem deletes by user and product', async () => {
    wishlistDeleteMany.mockResolvedValue({ count: 1 });

    await service.removeWishlistItem(userId, productId);

    expect(wishlistDeleteMany).toHaveBeenCalledWith({
      where: { userId, productId },
    });
  });

  it('removeWishlistItem throws 404 when nothing deleted', async () => {
    wishlistDeleteMany.mockResolvedValue({ count: 0 });

    await expect(service.removeWishlistItem(userId, productId)).rejects.toMatchObject(
      {
        response: { message: WISHLIST_ITEM_NOT_FOUND_MESSAGE },
      },
    );
  });
});
