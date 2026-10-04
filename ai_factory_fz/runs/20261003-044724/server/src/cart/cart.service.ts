import { BadRequestException, Injectable } from '@nestjs/common';
import type { ProductVariant } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service.js';
import { toCartResponse } from './cart.mapper.js';
import {
  CartLineInputDto,
  CartResponseDto,
  MergeCartStrategy,
} from './dto/cart.dto.js';

type VariantRow = ProductVariant & {
  product: { id: string; name: string; isActive: boolean };
};

type ResolvedLine = {
  variantId: string;
  quantity: number;
  variant: VariantRow;
};

const cartItemInclude = {
  variant: { select: { productId: true } },
} as const;

@Injectable()
export class CartService {
  constructor(private readonly prisma: PrismaService) {}

  async getCart(userId: string): Promise<CartResponseDto> {
    const cart = await this.ensureCart(userId);
    const items = await this.prisma.cartItem.findMany({
      where: { cartId: cart.id },
      include: cartItemInclude,
      orderBy: { createdAt: 'asc' },
    });
    return toCartResponse(items);
  }

  async replaceCart(
    userId: string,
    lines: CartLineInputDto[],
  ): Promise<CartResponseDto> {
    const aggregated = aggregateLines(lines);
    const resolved = await this.resolveLines(aggregated, {
      failOnInsufficientStock: true,
    });
    await this.persistCartLines(userId, resolved);
    return this.getCart(userId);
  }

  async mergeCart(
    userId: string,
    guestLines: CartLineInputDto[],
    strategy: MergeCartStrategy = MergeCartStrategy.MERGE,
  ): Promise<CartResponseDto> {
    if (strategy === MergeCartStrategy.GUEST_WINS) {
      return this.replaceCart(userId, guestLines);
    }

    const guestAggregated = aggregateLines(guestLines);
    const cart = await this.ensureCart(userId);
    const existing = await this.prisma.cartItem.findMany({
      where: { cartId: cart.id },
    });

    const combined = new Map<string, number>();
    for (const line of existing) {
      combined.set(line.variantId, line.quantity);
    }
    for (const [variantId, quantity] of guestAggregated) {
      combined.set(variantId, (combined.get(variantId) ?? 0) + quantity);
    }

    const capped = await this.capQuantitiesByStock(combined);
    const resolved = await this.resolveLines(capped, {
      failOnInsufficientStock: false,
    });
    await this.persistCartLines(userId, resolved);
    return this.getCart(userId);
  }

  private async ensureCart(userId: string): Promise<{ id: string }> {
    return this.prisma.cart.upsert({
      where: { userId },
      create: { userId },
      update: {},
      select: { id: true },
    });
  }

  private async persistCartLines(
    userId: string,
    lines: ResolvedLine[],
  ): Promise<void> {
    const cart = await this.ensureCart(userId);
    await this.prisma.$transaction(async (tx) => {
      await tx.cartItem.deleteMany({ where: { cartId: cart.id } });
      if (lines.length === 0) {
        return;
      }
      await tx.cartItem.createMany({
        data: lines.map((line) => ({
          cartId: cart.id,
          variantId: line.variantId,
          quantity: line.quantity,
          unitPriceCents: line.variant.priceCents,
          currency: line.variant.currency,
          productName: line.variant.product.name,
          variantName: line.variant.name,
        })),
      });
    });
  }

  private availableQuantity(variant: ProductVariant): number {
    return Math.max(0, variant.stockQuantity - variant.reservedQuantity);
  }

  private async capQuantitiesByStock(
    quantities: Map<string, number>,
  ): Promise<Map<string, number>> {
    if (quantities.size === 0) {
      return quantities;
    }
    const variants = await this.prisma.productVariant.findMany({
      where: { id: { in: [...quantities.keys()] } },
    });
    const byId = new Map(variants.map((v) => [v.id, v]));
    const capped = new Map<string, number>();
    for (const [variantId, requested] of quantities) {
      const variant = byId.get(variantId);
      if (variant === undefined || !variant.isActive) {
        continue;
      }
      const available = this.availableQuantity(variant);
      if (available <= 0) {
        continue;
      }
      capped.set(variantId, Math.min(requested, available));
    }
    return capped;
  }

  private async resolveLines(
    quantities: Map<string, number>,
    options: { failOnInsufficientStock: boolean },
  ): Promise<ResolvedLine[]> {
    if (quantities.size === 0) {
      return [];
    }

    const variants = await this.prisma.productVariant.findMany({
      where: { id: { in: [...quantities.keys()] } },
      include: {
        product: { select: { id: true, name: true, isActive: true } },
      },
    });
    const byId = new Map(variants.map((v) => [v.id, v]));

    const resolved: ResolvedLine[] = [];
    for (const [variantId, quantity] of quantities) {
      const variant = byId.get(variantId);
      if (variant === undefined) {
        throw new BadRequestException(`Unknown product variant: ${variantId}`);
      }
      if (!variant.isActive || !variant.product.isActive) {
        throw new BadRequestException(
          `Product variant is not available: ${variantId}`,
        );
      }
      const available = this.availableQuantity(variant);
      if (options.failOnInsufficientStock && quantity > available) {
        throw new BadRequestException(
          `Insufficient stock for variant ${variantId}`,
        );
      }
      if (available <= 0) {
        if (options.failOnInsufficientStock) {
          throw new BadRequestException(
            `Insufficient stock for variant ${variantId}`,
          );
        }
        continue;
      }
      const finalQty = options.failOnInsufficientStock
        ? quantity
        : Math.min(quantity, available);
      if (finalQty < 1) {
        continue;
      }
      resolved.push({ variantId, quantity: finalQty, variant });
    }
    return resolved;
  }
}

function aggregateLines(lines: CartLineInputDto[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const line of lines) {
    map.set(line.variantId, (map.get(line.variantId) ?? 0) + line.quantity);
  }
  return map;
}
