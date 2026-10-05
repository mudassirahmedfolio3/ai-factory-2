import { ApiProperty } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';
import { HomeBannerDto } from './home-banner.dto';
import { ProductSummaryDto } from './product-summary.dto';

export class HomeResponseDto {
  @ApiProperty({ type: [CategorySummaryDto] })
  categories!: CategorySummaryDto[];

  @ApiProperty({ type: [HomeBannerDto] })
  banners!: HomeBannerDto[];

  @ApiProperty({ type: [ProductSummaryDto] })
  featuredProducts!: ProductSummaryDto[];

  @ApiProperty({ type: [ProductSummaryDto] })
  newArrivals!: ProductSummaryDto[];
}
