import { Prisma } from '@prisma/client';
import { ProductWithRelations, toProductSummary } from '../catalog/catalog.mapper';
import { WishlistItemDto } from './dto/wishlist-item.dto';

export const wishlistProductInclude = {
  brand: { select: { name: true } },
  category: {
    select: { id: true, name: true, slug: true, parentId: true, imageUrl: true },
  },
  variants: {
    where: { isActive: true },
    orderBy: [
      { isDefault: Prisma.SortOrder.desc },
      { sku: Prisma.SortOrder.asc },
    ],
  },
} satisfies Prisma.ProductInclude;

export type WishlistItemWithProduct = {
  productId: string;
  createdAt: Date;
  product: ProductWithRelations;
};

export function toWishlistItem(row: WishlistItemWithProduct): WishlistItemDto {
  return {
    productId: row.productId,
    addedAt: row.createdAt.toISOString(),
    product: toProductSummary(row.product),
  };
}
