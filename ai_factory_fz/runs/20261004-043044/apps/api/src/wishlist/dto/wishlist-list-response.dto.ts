import { ApiProperty } from '@nestjs/swagger';
import { WishlistItemDto } from './wishlist-item.dto';

export class WishlistListResponseDto {
  @ApiProperty({ type: [WishlistItemDto] })
  items!: WishlistItemDto[];

  @ApiProperty()
  total!: number;

  @ApiProperty({ minimum: 1 })
  page!: number;

  @ApiProperty({ minimum: 1, maximum: 50 })
  pageSize!: number;
}
