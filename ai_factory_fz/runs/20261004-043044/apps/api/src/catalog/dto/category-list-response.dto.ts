import { ApiProperty } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';

export class CategoryListResponseDto {
  @ApiProperty({ type: [CategorySummaryDto] })
  items!: CategorySummaryDto[];
}
