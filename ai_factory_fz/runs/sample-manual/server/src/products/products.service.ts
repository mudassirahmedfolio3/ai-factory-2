// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export class ProductsService {
  constructor(private readonly prisma: PrismaService) {}

  async list(page: number, pageSize: number) {
    const [items, total] = await Promise.all([
      this.prisma.product.findMany({ skip: (page - 1) * pageSize, take: pageSize, orderBy: { name: 'asc' } }),
      this.prisma.product.count(),
    ]);
    return { items, page, pageSize, total };
  }

  findOne(id: string) {
    return this.prisma.product.findUnique({ where: { id } });
  }
}
