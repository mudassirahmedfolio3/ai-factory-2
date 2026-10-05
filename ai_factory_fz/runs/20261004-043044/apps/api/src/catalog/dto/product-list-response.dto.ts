import { ApiProperty } from '@nestjs/swagger';
import { ProductSummaryDto } from './product-summary.dto';

export class ProductListResponseDto {
  @ApiProperty({ type: [ProductSummaryDto] })
  items!: ProductSummaryDto[];

  @ApiProperty({ minimum: 0 })
  total!: number;

  @ApiProperty({ minimum: 1 })
  page!: number;

  @ApiProperty({ minimum: 1 })
  pageSize!: number;
}
