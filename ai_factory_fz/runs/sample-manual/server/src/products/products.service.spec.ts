// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { ProductsService } from './products.service';

describe('ProductsService', () => {
  const rows = [{ id: 'p1', name: 'Shoe', priceCents: 5900, imageUrl: 'u', description: 'd' }];
  const prisma: any = {
    product: {
      findMany: jest.fn().mockResolvedValue(rows),
      count: jest.fn().mockResolvedValue(1),
      findUnique: jest.fn().mockImplementation(({ where }) => rows.find((r) => r.id === where.id) ?? null),
    },
  };
  const service = new ProductsService(prisma);

  it('returns a page with the total', async () => {
    expect(await service.list(1, 20)).toEqual({ items: rows, page: 1, pageSize: 20, total: 1 });
  });

  it('returns null for an unknown product', async () => {
    expect(await service.findOne('nope')).toBeNull();
  });
});
