// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class CartService {
  constructor(private readonly prisma: PrismaService) {}

  async getCart(deviceId: string) {
    const cart = await this.prisma.cart.upsert({
      where: { deviceId },
      create: { deviceId },
      update: {},
      include: { items: { include: { product: true } } },
    });
    const items = cart.items.map((i) => ({
      productId: i.productId,
      name: i.product.name,
      unitPriceCents: i.product.priceCents,
      quantity: i.quantity,
      lineTotalCents: i.product.priceCents * i.quantity,
    }));
    return { items, totalCents: items.reduce((sum, i) => sum + i.lineTotalCents, 0) };
  }

  async addItem(deviceId: string, productId: string) {
    const product = await this.prisma.product.findUnique({ where: { id: productId } });
    if (!product) throw new NotFoundException({ code: 'NOT_FOUND', message: 'Product not found' });
    const cart = await this.prisma.cart.upsert({ where: { deviceId }, create: { deviceId }, update: {} });
    await this.prisma.cartItem.upsert({
      where: { cartId_productId: { cartId: cart.id, productId } },
      create: { cartId: cart.id, productId, quantity: 1 },
      update: { quantity: { increment: 1 } },
    });
    return this.getCart(deviceId);
  }

  async setQuantity(deviceId: string, productId: string, quantity: number) {
    const cart = await this.prisma.cart.findUnique({ where: { deviceId } });
    const existing = cart
      ? await this.prisma.cartItem.findUnique({ where: { cartId_productId: { cartId: cart.id, productId } } })
      : null;
    if (!cart || !existing) throw new NotFoundException({ code: 'NOT_FOUND', message: 'Item is not in the cart' });
    if (quantity === 0) {
      await this.prisma.cartItem.delete({ where: { cartId_productId: { cartId: cart.id, productId } } });
    } else {
      await this.prisma.cartItem.update({
        where: { cartId_productId: { cartId: cart.id, productId } },
        data: { quantity },
      });
    }
    return this.getCart(deviceId);
  }
}
