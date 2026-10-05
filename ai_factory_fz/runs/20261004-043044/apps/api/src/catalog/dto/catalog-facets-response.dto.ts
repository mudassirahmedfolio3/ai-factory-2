import { ApiProperty } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';

export class BrandFacetDto {
  @ApiProperty()
  name!: string;

  @ApiProperty({ minimum: 0 })
  productCount!: number;
}

export class WattageFacetDto {
  @ApiProperty()
  minW!: number;

  @ApiProperty()
  maxW!: number;
}

export class PriceFacetDto {
  @ApiProperty()
  minPriceCents!: number;

  @ApiProperty()
  maxPriceCents!: number;
}

export class CatalogFacetsResponseDto {
  @ApiProperty({ type: [BrandFacetDto] })
  brands!: BrandFacetDto[];

  @ApiProperty({ type: [String] })
  finishes!: string[];

  @ApiProperty({ type: WattageFacetDto })
  wattage!: WattageFacetDto;

  @ApiProperty({ type: PriceFacetDto })
  price!: PriceFacetDto;

  @ApiProperty({ type: [CategorySummaryDto] })
  categories!: CategorySummaryDto[];
}
