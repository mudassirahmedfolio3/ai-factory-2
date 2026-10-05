import { ApiProperty } from '@nestjs/swagger';

export class RatingSummaryDto {
  @ApiProperty({ minimum: 0, maximum: 5, example: 4.5 })
  averageRating!: number;

  @ApiProperty({ minimum: 0, example: 12 })
  reviewCount!: number;
}
