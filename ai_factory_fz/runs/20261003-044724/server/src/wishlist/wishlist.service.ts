import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import type { WishlistResponseDto } from './dto/wishlist.dto.js';

@Injectable()
export class WishlistService {
  constructor(private readonly prisma: PrismaService) {}

  async getWishlist(userId: string): Promise<WishlistResponseDto> {
    const wishlist = await this.ensureWishlist(userId);
    const items = await this.prisma.wishlistItem.findMany({
      where: { wishlistId: wishlist.id },
      orderBy: { createdAt: 'asc' },
    });
    return {
      items: items.map((item) => ({
        productId: item.productId,
        addedAt: item.createdAt.toISOString(),
      })),
    };
  }

  async replaceWishlist(
    userId: string,
    productIds: string[],
  ): Promise<WishlistResponseDto> {
    const uniqueIds = dedupePreserveOrder(productIds);
    const validIds = await this.filterActiveProductIds(uniqueIds);
    const wishlist = await this.ensureWishlist(userId);

    await this.prisma.$transaction(async (tx) => {
      await tx.wishlistItem.deleteMany({ where: { wishlistId: wishlist.id } });
      if (validIds.length > 0) {
        await tx.wishlistItem.createMany({
          data: validIds.map((productId) => ({
            wishlistId: wishlist.id,
            productId,
          })),
        });
      }
    });

    return this.getWishlist(userId);
  }

  async importWishlist(
    userId: string,
    productIds: string[],
  ): Promise<WishlistResponseDto> {
    const uniqueIncoming = dedupePreserveOrder(productIds);
    const validIncoming = await this.filterActiveProductIds(uniqueIncoming);
    if (validIncoming.length === 0) {
      return this.getWishlist(userId);
    }

    const wishlist = await this.ensureWishlist(userId);
    const existing = await this.prisma.wishlistItem.findMany({
      where: { wishlistId: wishlist.id },
      select: { productId: true },
    });
    const existingSet = new Set(existing.map((row) => row.productId));
    const toAdd = validIncoming.filter((id) => !existingSet.has(id));

    if (toAdd.length > 0) {
      await this.prisma.wishlistItem.createMany({
        data: toAdd.map((productId) => ({
          wishlistId: wishlist.id,
          productId,
        })),
        skipDuplicates: true,
      });
    }

    return this.getWishlist(userId);
  }

  private async ensureWishlist(userId: string): Promise<{ id: string }> {
    return this.prisma.wishlist.upsert({
      where: { userId },
      create: { userId },
      update: {},
      select: { id: true },
    });
  }

  private async filterActiveProductIds(productIds: string[]): Promise<string[]> {
    if (productIds.length === 0) {
      return [];
    }
    const products = await this.prisma.product.findMany({
      where: { id: { in: productIds }, isActive: true },
      select: { id: true },
    });
    const active = new Set(products.map((p) => p.id));
    return productIds.filter((id) => active.has(id));
  }
}

function dedupePreserveOrder(ids: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const id of ids) {
    if (seen.has(id)) {
      continue;
    }
    seen.add(id);
    result.push(id);
  }
  return result;
}
