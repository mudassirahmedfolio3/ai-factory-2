import { ApiProperty } from '@nestjs/swagger';

export class ReviewDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ minimum: 1, maximum: 5 })
  rating!: number;

  @ApiProperty()
  title!: string;

  @ApiProperty()
  body!: string;

  @ApiProperty({ example: 'Verified Buyer' })
  authorDisplayName!: string;

  @ApiProperty({ format: 'date-time' })
  createdAt!: string;
}
