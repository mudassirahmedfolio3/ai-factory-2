// SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
import { BadRequestException, Controller, Get, NotFoundException, Param, Query } from '@nestjs/common';
import { ProductsService } from './products.service';

@Controller('products')
export class ProductsController {
  constructor(private readonly products: ProductsService) {}

  /** listProducts: GET /products?page&pageSize -> ProductPage */
  @Get()
  list(@Query('page') page = '1', @Query('pageSize') pageSize = '20') {
    const p = Number(page);
    const size = Number(pageSize);
    if (!Number.isInteger(p) || p < 1 || !Number.isInteger(size) || size < 1 || size > 100) {
      throw new BadRequestException({ code: 'VALIDATION_ERROR', message: 'page must be >= 1 and pageSize 1-100' });
    }
    return this.products.list(p, size);
  }

  /** getProduct: GET /products/{id} -> Product, 404 when unknown */
  @Get(':id')
  async get(@Param('id') id: string) {
    const product = await this.products.findOne(id);
    if (!product) throw new NotFoundException({ code: 'NOT_FOUND', message: 'Product not found' });
    return product;
  }
}
