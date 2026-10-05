import { Injectable, NotFoundException } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { PaginationQueryDto } from '../catalog/dto/pagination-query.dto';
import { AddWishlistItemRequestDto } from './dto/add-wishlist-item-request.dto';
import { WishlistItemDto } from './dto/wishlist-item.dto';
import { WishlistListResponseDto } from './dto/wishlist-list-response.dto';
import {
  WISHLIST_ITEM_NOT_FOUND_MESSAGE,
  WISHLIST_PRODUCT_NOT_FOUND_MESSAGE,
} from './wishlist.constants';
import {
  toWishlistItem,
  wishlistProductInclude,
  WishlistItemWithProduct,
} from './wishlist.mapper';

const wishlistItemInclude = {
  product: { include: wishlistProductInclude },
} satisfies Prisma.WishlistItemInclude;

type WishlistRow = Prisma.WishlistItemGetPayload<{
  include: typeof wishlistItemInclude;
}>;

@Injectable()
export class WishlistService {
  constructor(private readonly prisma: PrismaService) {}

  async listWishlist(
    userId: string,
    query: PaginationQueryDto,
  ): Promise<WishlistListResponseDto> {
    const skip = (query.page - 1) * query.pageSize;
    const where = { userId };

    const [total, rows] = await Promise.all([
      this.prisma.wishlistItem.count({ where }),
      this.prisma.wishlistItem.findMany({
        where,
        skip,
        take: query.pageSize,
        orderBy: { createdAt: Prisma.SortOrder.desc },
        include: wishlistItemInclude,
      }),
    ]);

    return {
      items: rows.map((row) => toWishlistItem(this.asWishlistItemWithProduct(row))),
      total,
      page: query.page,
      pageSize: query.pageSize,
    };
  }

  async addWishlistItem(
    userId: string,
    dto: AddWishlistItemRequestDto,
  ): Promise<WishlistItemDto> {
    const product = await this.prisma.product.findFirst({
      where: { id: dto.productId, isActive: true },
      include: wishlistProductInclude,
    });

    if (!product) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: WISHLIST_PRODUCT_NOT_FOUND_MESSAGE,
      });
    }

    const existing = await this.prisma.wishlistItem.findUnique({
      where: {
        userId_productId: { userId, productId: dto.productId },
      },
      include: wishlistItemInclude,
    });

    if (existing) {
      return toWishlistItem(this.asWishlistItemWithProduct(existing));
    }

    const created = await this.prisma.wishlistItem.create({
      data: { userId, productId: dto.productId },
      include: wishlistItemInclude,
    });

    return toWishlistItem(this.asWishlistItemWithProduct(created));
  }

  async removeWishlistItem(userId: string, productId: string): Promise<void> {
    const result = await this.prisma.wishlistItem.deleteMany({
      where: { userId, productId },
    });

    if (result.count === 0) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: WISHLIST_ITEM_NOT_FOUND_MESSAGE,
      });
    }
  }

  private asWishlistItemWithProduct(row: WishlistRow): WishlistItemWithProduct {
    return {
      productId: row.productId,
      createdAt: row.createdAt,
      product: row.product,
    };
  }
}
