import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';
import { MoneyDto } from './money.dto';
import { RatingSummaryDto } from './rating-summary.dto';

export class ProductSummaryDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ example: 'Modern LED Ceiling Light' })
  name!: string;

  @ApiProperty({ example: 'Luminex' })
  brand!: string;

  @ApiProperty()
  slug!: string;

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

  @ApiProperty({ type: RatingSummaryDto })
  rating!: RatingSummaryDto;

  @ApiPropertyOptional({ minimum: 1, nullable: true })
  popularityRank?: number | null;
}
