import {
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Query,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiHeader,
  ApiOperation,
  ApiParam,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthenticatedUser } from '../auth/auth-user.type';
import { CurrentUser } from '../auth/current-user.decorator';
import { OptionalJwtAuthGuard } from '../auth/optional-jwt-auth.guard';
import { GuestCartIdHeader } from '../cart/guest-cart-id.decorator';
import { CatalogService } from './catalog.service';
import { CatalogFacetsQueryDto } from './dto/catalog-facets-query.dto';
import { CatalogFacetsResponseDto } from './dto/catalog-facets-response.dto';
import { CategoryDetailDto } from './dto/category-detail.dto';
import { CategoryListResponseDto } from './dto/category-list-response.dto';
import { HomeResponseDto } from './dto/home-response.dto';
import { ListCategoriesQueryDto } from './dto/list-categories-query.dto';
import { ListProductsQueryDto } from './dto/list-products-query.dto';
import { PaginationQueryDto } from './dto/pagination-query.dto';
import { ProductDetailDto } from './dto/product-detail.dto';
import { ProductListResponseDto } from './dto/product-list-response.dto';
import { ReviewListResponseDto } from './dto/review-list-response.dto';

@ApiTags('Catalog')
@Controller()
export class CatalogController {
  constructor(private readonly catalogService: CatalogService) {}

  @Get('home')
  @ApiOperation({
    operationId: 'getHome',
    summary: 'Home merchandising payload',
    description:
      'Top-level categories, merchandising banners, featured products, and new arrivals for the home screen (US-001).',
  })
  @ApiResponse({ status: 200, type: HomeResponseDto })
  getHome(): Promise<HomeResponseDto> {
    return this.catalogService.getHome();
  }

  @Get('categories')
  @ApiOperation({
    operationId: 'listCategories',
    summary: 'List category tree',
    description:
      'Returns active categories with optional parent relationships for browse paths (US-001).',
  })
  @ApiResponse({ status: 200, type: CategoryListResponseDto })
  listCategories(
    @Query() query: ListCategoriesQueryDto,
  ): Promise<CategoryListResponseDto> {
    return this.catalogService.listCategories(query.depth);
  }

  @Get('categories/:slug')
  @ApiOperation({
    operationId: 'getCategoryBySlug',
    summary: 'Get category by slug',
    description:
      'Resolve a category or subcategory for listing context (US-001).',
  })
  @ApiParam({ name: 'slug', schema: { type: 'string', maxLength: 100 } })
  @ApiResponse({ status: 200, type: CategoryDetailDto })
  @ApiResponse({ status: 404, description: 'Category not found' })
  getCategoryBySlug(@Param('slug') slug: string): Promise<CategoryDetailDto> {
    return this.catalogService.getCategoryBySlug(slug);
  }

  @Get('catalog/facets')
  @ApiOperation({
    operationId: 'getCatalogFacets',
    summary: 'Filter facet metadata',
    description:
      'Brands, finishes, wattage bounds, and category options for the listing filter UI (US-003).',
  })
  @ApiResponse({ status: 200, type: CatalogFacetsResponseDto })
  getCatalogFacets(
    @Query() query: CatalogFacetsQueryDto,
  ): Promise<CatalogFacetsResponseDto> {
    return this.catalogService.getCatalogFacets(query);
  }

  @Get('products')
  @ApiOperation({
    operationId: 'listProducts',
    summary: 'List and search products',
    description:
      'Paginated product listing with text search (name, SKU, brand, keywords), filters, and sort (US-001, US-002, US-003). Prices in pence GBP.',
  })
  @ApiResponse({ status: 200, type: ProductListResponseDto })
  @ApiResponse({ status: 400, description: 'Invalid query' })
  listProducts(
    @Query() query: ListProductsQueryDto,
  ): Promise<ProductListResponseDto> {
    return this.catalogService.listProducts(query);
  }

  @Get('products/:productId')
  @UseGuards(OptionalJwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({
    operationId: 'getProductById',
    summary: 'Product detail',
    description:
      'Detail with variants, lighting specifications, images, and ratings summary (US-004).',
  })
  @ApiHeader({
    name: 'X-Guest-Cart-Id',
    required: false,
    schema: { type: 'string', format: 'uuid' },
    description:
      'Optional guest cart id used as analytics session correlation when persistence is enabled (NFR-10).',
  })
  @ApiParam({ name: 'productId', format: 'uuid' })
  @ApiResponse({ status: 200, type: ProductDetailDto })
  @ApiResponse({ status: 404, description: 'Not found' })
  getProductById(
    @Param('productId', ParseUUIDPipe) productId: string,
    @CurrentUser() user: AuthenticatedUser | null,
    @GuestCartIdHeader() guestCartId?: string,
  ): Promise<ProductDetailDto> {
    return this.catalogService.getProductById(productId, {
      userId: user?.id ?? null,
      sessionId: guestCartId ?? null,
    });
  }

  @Get('products/:productId/reviews')
  @ApiOperation({
    operationId: 'listProductReviews',
    summary: 'List product reviews',
    description: 'Paginated reviews for product detail (US-004).',
  })
  @ApiParam({ name: 'productId', format: 'uuid' })
  @ApiResponse({ status: 200, type: ReviewListResponseDto })
  @ApiResponse({ status: 404, description: 'Product not found' })
  listProductReviews(
    @Param('productId', ParseUUIDPipe) productId: string,
    @Query() query: PaginationQueryDto,
  ): Promise<ReviewListResponseDto> {
    return this.catalogService.listProductReviews(productId, query);
  }
}
