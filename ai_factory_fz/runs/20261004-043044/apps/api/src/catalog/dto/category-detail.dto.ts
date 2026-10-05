import { ApiPropertyOptional } from '@nestjs/swagger';
import { CategorySummaryDto } from './category-summary.dto';

export class CategoryDetailDto extends CategorySummaryDto {
  @ApiPropertyOptional()
  description?: string;

  @ApiPropertyOptional({ type: [CategorySummaryDto] })
  children?: CategorySummaryDto[];
}
