import { Controller, Get, Param, ParseUUIDPipe, Query } from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
} from '@nestjs/swagger';
import { CatalogService } from './catalog.service.js';
import {
  CategoryListResponse,
  ProductDetailResponse,
  ProductListResponse,
} from './dto/catalog.responses.js';
import { ListProductsQueryDto } from './dto/list-products.query.js';

@ApiTags('Catalog')
@Controller()
export class CatalogController {
  constructor(private readonly catalogService: CatalogService) {}

  @Get('categories')
  @ApiOperation({
    operationId: 'listCategories',
    summary: 'List product categories',
  })
  @ApiOkResponse({
    type: CategoryListResponse,
    description: 'Category list',
  })
  listCategories(): Promise<CategoryListResponse> {
    return this.catalogService.listCategories();
  }

  @Get('products')
  @ApiOperation({
    operationId: 'listProducts',
    summary: 'List and search products',
  })
  @ApiOkResponse({
    type: ProductListResponse,
    description: 'Paginated products',
  })
  @ApiBadRequestResponse({
    schema: {
      type: 'object',
      properties: {
        statusCode: { type: 'integer', example: 400 },
        error: { type: 'string', example: 'Bad Request' },
        message: { type: 'string', example: 'Validation failed' },
      },
      required: ['statusCode', 'error', 'message'],
    },
  })
  listProducts(
    @Query() query: ListProductsQueryDto,
  ): Promise<ProductListResponse> {
    return this.catalogService.listProducts(query);
  }

  @Get('products/:productId')
  @ApiOperation({
    operationId: 'getProductById',
    summary: 'Get product detail',
  })
  @ApiOkResponse({
    type: ProductDetailResponse,
    description: 'Product detail',
  })
  @ApiNotFoundResponse({
    schema: {
      type: 'object',
      properties: {
        statusCode: { type: 'integer', example: 404 },
        error: { type: 'string', example: 'Not Found' },
        message: { type: 'string', example: "Product with id '...' was not found" },
      },
      required: ['statusCode', 'error', 'message'],
    },
  })
  getProductById(
    @Param('productId', ParseUUIDPipe) productId: string,
  ): Promise<ProductDetailResponse> {
    return this.catalogService.getProductById(productId);
  }
}
