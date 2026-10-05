import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  CategoryResponse,
  ProductSummaryResponse,
} from '../../catalog/dto/catalog.responses.js';

export class HomeBannerResponse {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  title!: string;

  @ApiPropertyOptional()
  subtitle?: string;

  @ApiProperty({ format: 'uri' })
  imageUrl!: string;

  @ApiPropertyOptional()
  ctaLabel?: string;

  @ApiPropertyOptional()
  categorySlug?: string;
}

export class HomeResponse {
  @ApiProperty({ type: [HomeBannerResponse] })
  banners!: HomeBannerResponse[];

  @ApiProperty({ type: [ProductSummaryResponse] })
  featured!: ProductSummaryResponse[];

  @ApiProperty({ type: [ProductSummaryResponse] })
  newArrivals!: ProductSummaryResponse[];

  @ApiProperty({ type: [CategoryResponse] })
  categories!: CategoryResponse[];
}
