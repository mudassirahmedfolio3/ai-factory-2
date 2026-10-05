import { ApiProperty } from '@nestjs/swagger';
import { RatingSummaryDto } from './rating-summary.dto';
import { ReviewDto } from './review.dto';

export class ReviewListResponseDto {
  @ApiProperty({ type: [ReviewDto] })
  items!: ReviewDto[];

  @ApiProperty({ minimum: 0 })
  total!: number;

  @ApiProperty({ minimum: 1 })
  page!: number;

  @ApiProperty({ minimum: 1 })
  pageSize!: number;

  @ApiProperty({ type: RatingSummaryDto })
  rating!: RatingSummaryDto;
}
