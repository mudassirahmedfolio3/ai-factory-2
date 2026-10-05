import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';
import { LightingSpecsDto } from './lighting-specs.dto';
import { MoneyDto } from './money.dto';
import { ProductImageDto } from './product-image.dto';
import { ProductVariantDto } from './product-variant.dto';
import { RatingSummaryDto } from './rating-summary.dto';

export class ProductDetailDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  name!: string;

  @ApiProperty()
  brand!: string;

  @ApiProperty()
  slug!: string;

  @ApiProperty()
  description!: string;

  @ApiProperty({ type: CategorySummaryDto })
  category!: CategorySummaryDto;

  @ApiProperty({ type: MoneyDto })
  price!: MoneyDto;

  @ApiPropertyOptional({ type: MoneyDto, nullable: true })
  compareAtPrice?: MoneyDto | null;

  @ApiProperty({ format: 'uri' })
  primaryImageUrl!: string;

  @ApiProperty()
  inStock!: boolean;

  @ApiProperty({ type: [ProductVariantDto], minItems: 1 })
  variants!: ProductVariantDto[];

  @ApiProperty({ type: [ProductImageDto] })
  images!: ProductImageDto[];

  @ApiProperty({ type: LightingSpecsDto })
  specs!: LightingSpecsDto;

  @ApiProperty({ type: RatingSummaryDto })
  rating!: RatingSummaryDto;

  @ApiPropertyOptional({ minimum: 1, nullable: true })
  popularityRank?: number | null;

  @ApiPropertyOptional({ minimum: 0 })
  unitsSold90Days?: number;
}
