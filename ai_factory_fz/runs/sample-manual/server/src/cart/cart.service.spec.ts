// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { NotFoundException } from '@nestjs/common';
import { CartService } from './cart.service';

describe('CartService', () => {
  it('rejects adding an unknown product', async () => {
    const prisma: any = { product: { findUnique: jest.fn().mockResolvedValue(null) } };
    await expect(new CartService(prisma).addItem('d1', 'nope')).rejects.toBeInstanceOf(NotFoundException);
  });

  it('totals line items in cents', async () => {
    const prisma: any = {
      cart: {
        upsert: jest.fn().mockResolvedValue({
          items: [{ productId: 'p1', quantity: 2, product: { name: 'Shoe', priceCents: 1000 } }],
        }),
      },
    };
    expect(await new CartService(prisma).getCart('d1')).toEqual({
      items: [{ productId: 'p1', name: 'Shoe', unitPriceCents: 1000, quantity: 2, lineTotalCents: 2000 }],
      totalCents: 2000,
    });
  });
});
