import {
  BadRequestException,
  ConflictException,
  NotFoundException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { CartService } from './cart.service';
import { PrismaService } from '../prisma/prisma.service';
import { INSUFFICIENT_STOCK_MESSAGE } from './cart.constants';

const userId = '11111111-1111-4111-8111-111111111111';
const cartId = 'c1111111-1111-4111-8111-111111111111';
const guestCartId = 'a1111111-1111-4111-8111-111111111111';
const variantId = 'b1111111-1111-4111-8111-111111111111';
const itemId = 'd1111111-1111-4111-8111-111111111111';

describe('CartService', () => {
  let service: CartService;
  let cartFindUnique: jest.Mock;
  let cartCreate: jest.Mock;
  let cartItemCreate: jest.Mock;
  let cartItemUpdate: jest.Mock;
  let cartItemDelete: jest.Mock;
  let cartItemFindUnique: jest.Mock;
  let guestCartFindUnique: jest.Mock;
  let guestCartCreate: jest.Mock;
  let guestCartUpdate: jest.Mock;
  let guestCartDelete: jest.Mock;
  let guestCartItemCreate: jest.Mock;
  let guestCartItemUpdate: jest.Mock;
  let guestCartItemDelete: jest.Mock;
  let productVariantFindFirst: jest.Mock;
  let transaction: jest.Mock;

  const variant = {
    id: variantId,
    productId: 'p1111111-1111-4111-8111-111111111111',
    sku: 'CL-1001-WH',
    label: 'White',
    priceCents: 4999,
    currency: 'GBP',
    stockQuantity: 5,
    reservedQuantity: 1,
    imageUrl: null,
    isActive: true,
    product: {
      id: 'p1111111-1111-4111-8111-111111111111',
      name: 'Modern LED Ceiling Light',
      primaryImageUrl: 'assets/product.png',
      isActive: true,
    },
  };

  const emptyUserCart = {
    id: cartId,
    userId,
    createdAt: new Date(),
    updatedAt: new Date(),
    items: [],
  };

  beforeEach(() => {
    cartFindUnique = jest.fn();
    cartCreate = jest.fn();
    cartItemCreate = jest.fn();
    cartItemUpdate = jest.fn();
    cartItemDelete = jest.fn();
    cartItemFindUnique = jest.fn();
    guestCartFindUnique = jest.fn();
    guestCartCreate = jest.fn();
    guestCartUpdate = jest.fn();
    guestCartDelete = jest.fn();
    guestCartItemCreate = jest.fn();
    guestCartItemUpdate = jest.fn();
    guestCartItemDelete = jest.fn();
    productVariantFindFirst = jest.fn();
    transaction = jest.fn(async (fn: (tx: unknown) => Promise<void>) =>
      fn({
        productVariant: { findFirst: productVariantFindFirst },
        cartItem: {
          findUnique: cartItemFindUnique,
          update: cartItemUpdate,
          create: cartItemCreate,
        },
        guestCart: { delete: guestCartDelete },
      }),
    );

    const prisma = {
      cart: {
        findUnique: cartFindUnique,
        create: cartCreate,
      },
      cartItem: {
        create: cartItemCreate,
        update: cartItemUpdate,
        delete: cartItemDelete,
        findUnique: cartItemFindUnique,
      },
      guestCart: {
        findUnique: guestCartFindUnique,
        create: guestCartCreate,
        update: guestCartUpdate,
        delete: guestCartDelete,
      },
      guestCartItem: {
        create: guestCartItemCreate,
        update: guestCartItemUpdate,
        delete: guestCartItemDelete,
      },
      productVariant: {
        findFirst: productVariantFindFirst,
      },
      $transaction: transaction,
    } as unknown as PrismaService;

    service = new CartService(prisma, {
      get: () => undefined,
    } as ConfigService);
  });

  it('creates a guest cart on getCart when no header is provided', async () => {
    guestCartCreate.mockResolvedValue({
      id: guestCartId,
      expiresAt: new Date(Date.now() + 60_000),
      items: [],
    });

    const result = await service.getCart(null);

    expect(guestCartCreate).toHaveBeenCalled();
    expect(result.id).toBe(guestCartId);
    expect(result.guestCartId).toBe(guestCartId);
    expect(result.itemCount).toBe(0);
  });

  it('rejects add when quantity exceeds available stock', async () => {
    cartFindUnique.mockResolvedValue(emptyUserCart);
    productVariantFindFirst.mockResolvedValue(variant);

    await expect(
      service.addCartItem(userId, undefined, { variantId, quantity: 5 }),
    ).rejects.toMatchObject({
      response: { statusCode: 409, message: INSUFFICIENT_STOCK_MESSAGE },
    });
  });

  it('adds a line to the signed-in cart with price snapshot', async () => {
    cartFindUnique
      .mockResolvedValueOnce(emptyUserCart)
      .mockResolvedValueOnce({
        ...emptyUserCart,
        items: [
          {
            id: itemId,
            cartId,
            variantId,
            quantity: 2,
            unitPriceCents: 4999,
            currency: 'GBP',
            productName: variant.product.name,
            variantLabel: variant.label,
            sku: variant.sku,
            variant,
          },
        ],
      });
    productVariantFindFirst.mockResolvedValue(variant);
    cartItemCreate.mockResolvedValue({ id: itemId });

    const result = await service.addCartItem(userId, undefined, {
      variantId,
      quantity: 2,
    });

    expect(cartItemCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          unitPriceCents: 4999,
          quantity: 2,
        }),
      }),
    );
    expect(result.subtotalCents).toBe(9998);
    expect(result.items[0].productName).toBe('Modern LED Ceiling Light');
  });

  it('returns 404 when updating a missing cart item', async () => {
    cartFindUnique.mockResolvedValue(emptyUserCart);

    await expect(
      service.updateCartItem(userId, undefined, itemId, { quantity: 1 }),
    ).rejects.toBeInstanceOf(NotFoundException);
  });

  it('merges guest lines into the user cart and deletes guest cart', async () => {
    const future = new Date(Date.now() + 60_000);
    guestCartFindUnique.mockResolvedValue({
      id: guestCartId,
      expiresAt: future,
      items: [
        {
          id: 'g-item-1',
          guestCartId,
          variantId,
          quantity: 2,
          unitPriceCents: 4999,
          currency: 'GBP',
          productName: 'Modern LED Ceiling Light',
          variantLabel: 'White',
          sku: 'CL-1001-WH',
        },
      ],
    });
    cartFindUnique
      .mockResolvedValueOnce(emptyUserCart)
      .mockResolvedValueOnce({
        ...emptyUserCart,
        items: [
          {
            id: itemId,
            cartId,
            variantId,
            quantity: 2,
            unitPriceCents: 4999,
            currency: 'GBP',
            productName: 'Modern LED Ceiling Light',
            variantLabel: 'White',
            sku: 'CL-1001-WH',
            variant,
          },
        ],
      });
    productVariantFindFirst.mockResolvedValue(variant);
    cartItemFindUnique.mockResolvedValue(null);
    cartItemCreate.mockResolvedValue({ id: itemId });

    const result = await service.mergeGuestCart(userId, guestCartId);

    expect(transaction).toHaveBeenCalled();
    expect(result.itemCount).toBe(2);
  });

  it('rejects merge for invalid guest cart id', async () => {
    await expect(service.mergeGuestCart(userId, 'not-a-uuid')).rejects.toBeInstanceOf(
      BadRequestException,
    );
  });

  it('rejects update when stock is insufficient', async () => {
    cartFindUnique.mockResolvedValue({
      ...emptyUserCart,
      items: [
        {
          id: itemId,
          cartId,
          variantId,
          quantity: 1,
          unitPriceCents: 4999,
          currency: 'GBP',
          productName: variant.product.name,
          variantLabel: variant.label,
          sku: variant.sku,
          variant,
        },
      ],
    });
    productVariantFindFirst.mockResolvedValue(variant);

    await expect(
      service.updateCartItem(userId, undefined, itemId, { quantity: 5 }),
    ).rejects.toBeInstanceOf(ConflictException);
  });
});
