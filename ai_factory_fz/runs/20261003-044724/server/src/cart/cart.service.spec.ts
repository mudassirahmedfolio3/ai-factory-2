import { BadRequestException } from '@nestjs/common';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CartService } from './cart.service.js';
import { MergeCartStrategy } from './dto/cart.dto.js';

describe('CartService', () => {
  const prisma = {
    cart: {
      upsert: vi.fn(),
    },
    cartItem: {
      findMany: vi.fn(),
      deleteMany: vi.fn(),
      createMany: vi.fn(),
    },
    productVariant: {
      findMany: vi.fn(),
    },
    $transaction: vi.fn(),
  };

  let service: CartService;

  const variantRow = {
    id: 'var-1',
    productId: 'prod-1',
    sku: 'SKU1',
    name: 'Default',
    priceCents: 1000,
    currency: 'USD',
    stockQuantity: 10,
    reservedQuantity: 2,
    imageUrl: null,
    isDefault: true,
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
    product: { id: 'prod-1', name: 'Widget', isActive: true },
  };

  beforeEach(() => {
    vi.resetAllMocks();
    prisma.$transaction.mockImplementation(
      async (fn: (tx: typeof prisma) => Promise<unknown>) => fn(prisma),
    );
    prisma.cart.upsert.mockResolvedValue({ id: 'cart-1' });
    service = new CartService(prisma as never);
  });

  it('returns an empty cart when no lines exist', async () => {
    prisma.cartItem.findMany.mockResolvedValue([]);

    const result = await service.getCart('user-1');

    expect(result).toEqual({
      items: [],
      subtotal: { amountCents: 0, currency: 'USD' },
    });
  });

  it('rejects replace when stock is insufficient', async () => {
    prisma.productVariant.findMany.mockResolvedValue([variantRow]);

    await expect(
      service.replaceCart('user-1', [{ variantId: 'var-1', quantity: 20 }]),
    ).rejects.toBeInstanceOf(BadRequestException);
  });

  it('merges guest lines by summing quantities and capping stock', async () => {
    prisma.cartItem.findMany
      .mockResolvedValueOnce([{ variantId: 'var-1', quantity: 3 }])
      .mockResolvedValueOnce([
        {
          id: 'line-1',
          cartId: 'cart-1',
          variantId: 'var-1',
          quantity: 8,
          unitPriceCents: 1000,
          currency: 'USD',
          productName: 'Widget',
          variantName: 'Default',
          createdAt: new Date(),
          updatedAt: new Date(),
          variant: { productId: 'prod-1' },
        },
      ]);
    prisma.productVariant.findMany
      .mockResolvedValueOnce([variantRow])
      .mockResolvedValueOnce([variantRow]);

    const result = await service.mergeCart(
      'user-1',
      [{ variantId: 'var-1', quantity: 10 }],
      MergeCartStrategy.MERGE,
    );

    expect(prisma.cartItem.createMany).toHaveBeenCalledWith({
      data: [
        expect.objectContaining({
          variantId: 'var-1',
          quantity: 8,
          unitPriceCents: 1000,
        }),
      ],
    });
    expect(result.items[0]?.quantity).toBe(8);
  });

  it('guest_wins strategy replaces the account cart with guest lines', async () => {
    prisma.productVariant.findMany.mockResolvedValue([variantRow]);
    prisma.cartItem.findMany.mockResolvedValue([]);

    await service.mergeCart(
      'user-1',
      [{ variantId: 'var-1', quantity: 2 }],
      MergeCartStrategy.GUEST_WINS,
    );

    expect(prisma.cartItem.deleteMany).toHaveBeenCalled();
    expect(prisma.cartItem.createMany).toHaveBeenCalledWith({
      data: [
        expect.objectContaining({
          variantId: 'var-1',
          quantity: 2,
        }),
      ],
    });
  });
});
