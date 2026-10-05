import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
  UnprocessableEntityException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Cart, GuestCart, Prisma } from '@prisma/client';
import { isUUID } from 'class-validator';
import { PrismaService } from '../prisma/prisma.service';
import {
  CART_ITEM_NOT_FOUND_MESSAGE,
  CHECKOUT_CART_EMPTY_MESSAGE,
  DEFAULT_GUEST_CART_TTL_SECONDS,
  INSUFFICIENT_STOCK_MESSAGE,
  INVALID_GUEST_CART_MESSAGE,
} from './cart.constants';
import { toCartResponse } from './cart.mapper';
import { AddCartItemRequestDto } from './dto/add-cart-item-request.dto';
import { CartResponseDto } from './dto/cart-response.dto';
import { UpdateCartItemRequestDto } from './dto/update-cart-item-request.dto';

const cartItemInclude = {
  variant: {
    include: {
      product: true,
    },
  },
} satisfies Prisma.CartItemInclude;

const guestCartItemInclude = {
  variant: {
    include: {
      product: true,
    },
  },
} satisfies Prisma.GuestCartItemInclude;

type UserCartWithItems = Cart & {
  items: Prisma.CartItemGetPayload<{ include: typeof cartItemInclude }>[];
};

type GuestCartWithItems = GuestCart & {
  items: Prisma.GuestCartItemGetPayload<{ include: typeof guestCartItemInclude }>[];
};

@Injectable()
export class CartService {
  private readonly guestCartTtlSeconds: number;

  constructor(
    private readonly prisma: PrismaService,
    configService: ConfigService,
  ) {
    this.guestCartTtlSeconds =
      configService.get<number>('GUEST_CART_TTL_SECONDS') ??
      DEFAULT_GUEST_CART_TTL_SECONDS;
  }

  async getCartForCheckout(
    userId: string | null,
    guestCartIdHeader?: string,
  ): Promise<CartResponseDto> {
    if (userId) {
      const cart = await this.prisma.cart.findUnique({
        where: { userId },
        include: { items: { include: cartItemInclude } },
      });
      if (!cart || cart.items.length === 0) {
        throw new UnprocessableEntityException({
          statusCode: 422,
          error: 'Unprocessable Entity',
          message: CHECKOUT_CART_EMPTY_MESSAGE,
        });
      }
      return toCartResponse(cart.id, cart.items);
    }

    if (!guestCartIdHeader || !isUUID(guestCartIdHeader)) {
      throw new UnprocessableEntityException({
        statusCode: 422,
        error: 'Unprocessable Entity',
        message: CHECKOUT_CART_EMPTY_MESSAGE,
      });
    }

    const guestCart = await this.prisma.guestCart.findUnique({
      where: { id: guestCartIdHeader },
      include: { items: { include: guestCartItemInclude } },
    });

    if (!guestCart || guestCart.expiresAt <= new Date() || guestCart.items.length === 0) {
      throw new UnprocessableEntityException({
        statusCode: 422,
        error: 'Unprocessable Entity',
        message: CHECKOUT_CART_EMPTY_MESSAGE,
      });
    }

    return toCartResponse(guestCart.id, guestCart.items, { guestCartId: guestCart.id });
  }

  async getCart(userId: string | null, guestCartIdHeader?: string): Promise<CartResponseDto> {
    if (userId) {
      const cart = await this.ensureUserCart(userId);
      return toCartResponse(cart.id, cart.items);
    }

    if (guestCartIdHeader && !isUUID(guestCartIdHeader)) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }

    const guestCart = await this.resolveGuestCart(guestCartIdHeader);
    return toCartResponse(guestCart.id, guestCart.items, { guestCartId: guestCart.id });
  }

  async addCartItem(
    userId: string | null,
    guestCartIdHeader: string | undefined,
    dto: AddCartItemRequestDto,
  ): Promise<CartResponseDto> {
    const variant = await this.loadActiveVariant(dto.variantId);
    const available = this.availableStock(variant);

    if (userId) {
      const cart = await this.ensureUserCart(userId);
      const existing = cart.items.find((item) => item.variantId === dto.variantId);
      const targetQty = (existing?.quantity ?? 0) + dto.quantity;
      this.assertQuantityAllowed(targetQty, available);

      if (existing) {
        await this.prisma.cartItem.update({
          where: { id: existing.id },
          data: { quantity: targetQty },
        });
      } else {
        await this.prisma.cartItem.create({
          data: this.snapshotFromVariant(cart.id, variant, dto.quantity),
        });
      }

      const updated = await this.ensureUserCart(userId);
      return toCartResponse(updated.id, updated.items);
    }

    const guestCart = await this.resolveGuestCartForMutation(guestCartIdHeader);
    const existing = guestCart.items.find((item) => item.variantId === dto.variantId);
    const targetQty = (existing?.quantity ?? 0) + dto.quantity;
    this.assertQuantityAllowed(targetQty, available);

    if (existing) {
      await this.prisma.guestCartItem.update({
        where: { id: existing.id },
        data: { quantity: targetQty },
      });
    } else {
      await this.prisma.guestCartItem.create({
        data: this.snapshotFromVariantGuest(guestCart.id, variant, dto.quantity),
      });
    }

    await this.touchGuestCart(guestCart.id);
    const updated = await this.loadGuestCart(guestCart.id);
    return toCartResponse(updated.id, updated.items, { guestCartId: updated.id });
  }

  async updateCartItem(
    userId: string | null,
    guestCartIdHeader: string | undefined,
    itemId: string,
    dto: UpdateCartItemRequestDto,
  ): Promise<CartResponseDto> {
    if (userId) {
      const cart = await this.ensureUserCart(userId);
      const line = cart.items.find((item) => item.id === itemId);
      if (!line) {
        throw new NotFoundException({
          statusCode: 404,
          error: 'Not Found',
          message: CART_ITEM_NOT_FOUND_MESSAGE,
        });
      }

      const variant = await this.loadActiveVariant(line.variantId);
      this.assertQuantityAllowed(dto.quantity, this.availableStock(variant));

      await this.prisma.cartItem.update({
        where: { id: itemId },
        data: { quantity: dto.quantity },
      });

      const updated = await this.ensureUserCart(userId);
      return toCartResponse(updated.id, updated.items);
    }

    const guestCart = await this.resolveGuestCartForMutation(guestCartIdHeader);
    const line = guestCart.items.find((item) => item.id === itemId);
    if (!line) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: CART_ITEM_NOT_FOUND_MESSAGE,
      });
    }

    const variant = await this.loadActiveVariant(line.variantId);
    this.assertQuantityAllowed(dto.quantity, this.availableStock(variant));

    await this.prisma.guestCartItem.update({
      where: { id: itemId },
      data: { quantity: dto.quantity },
    });

    await this.touchGuestCart(guestCart.id);
    const updated = await this.loadGuestCart(guestCart.id);
    return toCartResponse(updated.id, updated.items, { guestCartId: updated.id });
  }

  async removeCartItem(
    userId: string | null,
    guestCartIdHeader: string | undefined,
    itemId: string,
  ): Promise<CartResponseDto> {
    if (userId) {
      const cart = await this.ensureUserCart(userId);
      const line = cart.items.find((item) => item.id === itemId);
      if (!line) {
        throw new NotFoundException({
          statusCode: 404,
          error: 'Not Found',
          message: CART_ITEM_NOT_FOUND_MESSAGE,
        });
      }

      await this.prisma.cartItem.delete({ where: { id: itemId } });
      const updated = await this.ensureUserCart(userId);
      return toCartResponse(updated.id, updated.items);
    }

    const guestCart = await this.resolveGuestCartForMutation(guestCartIdHeader);
    const line = guestCart.items.find((item) => item.id === itemId);
    if (!line) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: CART_ITEM_NOT_FOUND_MESSAGE,
      });
    }

    await this.prisma.guestCartItem.delete({ where: { id: itemId } });
    await this.touchGuestCart(guestCart.id);
    const updated = await this.loadGuestCart(guestCart.id);
    return toCartResponse(updated.id, updated.items, { guestCartId: updated.id });
  }

  async mergeGuestCart(userId: string, guestCartIdHeader?: string): Promise<CartResponseDto> {
    if (!guestCartIdHeader || !isUUID(guestCartIdHeader)) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }

    const guestCart = await this.prisma.guestCart.findUnique({
      where: { id: guestCartIdHeader },
      include: { items: true },
    });

    if (!guestCart || guestCart.expiresAt <= new Date()) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }

    const userCart = await this.ensureUserCart(userId);

    await this.prisma.$transaction(async (tx) => {
      for (const guestLine of guestCart.items) {
        const variant = await tx.productVariant.findFirst({
          where: { id: guestLine.variantId, isActive: true },
        });
        if (!variant) {
          continue;
        }

        const available = this.availableStock(variant);
        if (available <= 0) {
          continue;
        }

        const existing = await tx.cartItem.findUnique({
          where: {
            cartId_variantId: {
              cartId: userCart.id,
              variantId: guestLine.variantId,
            },
          },
        });

        const combinedQty = Math.min(99, (existing?.quantity ?? 0) + guestLine.quantity, available);
        if (combinedQty <= 0) {
          continue;
        }

        if (existing) {
          await tx.cartItem.update({
            where: { id: existing.id },
            data: { quantity: combinedQty },
          });
        } else {
          await tx.cartItem.create({
            data: {
              cartId: userCart.id,
              variantId: guestLine.variantId,
              quantity: combinedQty,
              unitPriceCents: guestLine.unitPriceCents,
              currency: guestLine.currency,
              productName: guestLine.productName,
              variantLabel: guestLine.variantLabel,
              sku: guestLine.sku,
            },
          });
        }
      }

      await tx.guestCart.delete({ where: { id: guestCart.id } });
    });

    const merged = await this.ensureUserCart(userId);
    return toCartResponse(merged.id, merged.items);
  }

  private availableStock(variant: { stockQuantity: number; reservedQuantity: number }): number {
    return Math.max(0, variant.stockQuantity - variant.reservedQuantity);
  }

  private assertQuantityAllowed(quantity: number, available: number): void {
    if (quantity > available) {
      throw new ConflictException({
        statusCode: 409,
        error: 'Conflict',
        message: INSUFFICIENT_STOCK_MESSAGE,
      });
    }
  }

  private async loadActiveVariant(variantId: string) {
    const variant = await this.prisma.productVariant.findFirst({
      where: { id: variantId, isActive: true },
      include: { product: true },
    });

    if (!variant || !variant.product.isActive) {
      throw new NotFoundException({
        statusCode: 404,
        error: 'Not Found',
        message: 'Product variant not found',
      });
    }

    return variant;
  }

  private async ensureUserCart(userId: string): Promise<UserCartWithItems> {
    const existing = await this.prisma.cart.findUnique({
      where: { userId },
      include: { items: { include: cartItemInclude } },
    });

    if (existing) {
      return existing;
    }

    return this.prisma.cart.create({
      data: { userId },
      include: { items: { include: cartItemInclude } },
    });
  }

  private guestExpiresAt(): Date {
    return new Date(Date.now() + this.guestCartTtlSeconds * 1000);
  }

  private async createGuestCart(): Promise<GuestCartWithItems> {
    return this.prisma.guestCart.create({
      data: { expiresAt: this.guestExpiresAt() },
      include: { items: { include: guestCartItemInclude } },
    });
  }

  private async loadGuestCart(id: string): Promise<GuestCartWithItems> {
    const cart = await this.prisma.guestCart.findUnique({
      where: { id },
      include: { items: { include: guestCartItemInclude } },
    });
    if (!cart) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }
    return cart;
  }

  private async touchGuestCart(id: string): Promise<void> {
    await this.prisma.guestCart.update({
      where: { id },
      data: { expiresAt: this.guestExpiresAt() },
    });
  }

  private async resolveGuestCart(guestCartIdHeader?: string): Promise<GuestCartWithItems> {
    if (!guestCartIdHeader) {
      return this.createGuestCart();
    }

    const cart = await this.prisma.guestCart.findUnique({
      where: { id: guestCartIdHeader },
      include: { items: { include: guestCartItemInclude } },
    });

    if (!cart || cart.expiresAt <= new Date()) {
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }

    await this.touchGuestCart(cart.id);
    return this.loadGuestCart(cart.id);
  }

  private async resolveGuestCartForMutation(
    guestCartIdHeader?: string,
  ): Promise<GuestCartWithItems> {
    if (!guestCartIdHeader || !isUUID(guestCartIdHeader)) {
      if (!guestCartIdHeader) {
        return this.createGuestCart();
      }
      throw new BadRequestException({
        statusCode: 400,
        error: 'Bad Request',
        message: INVALID_GUEST_CART_MESSAGE,
      });
    }

    return this.resolveGuestCart(guestCartIdHeader);
  }

  private snapshotFromVariant(
    cartId: string,
    variant: Prisma.ProductVariantGetPayload<{ include: { product: true } }>,
    quantity: number,
  ) {
    return {
      cartId,
      variantId: variant.id,
      quantity,
      unitPriceCents: variant.priceCents,
      currency: variant.currency,
      productName: variant.product.name,
      variantLabel: variant.label,
      sku: variant.sku,
    };
  }

  private snapshotFromVariantGuest(
    guestCartId: string,
    variant: Prisma.ProductVariantGetPayload<{ include: { product: true } }>,
    quantity: number,
  ) {
    return {
      guestCartId,
      variantId: variant.id,
      quantity,
      unitPriceCents: variant.priceCents,
      currency: variant.currency,
      productName: variant.product.name,
      variantLabel: variant.label,
      sku: variant.sku,
    };
  }
}
