import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { CartLineItemDto } from './cart-line-item.dto';

export class CartResponseDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiPropertyOptional({ format: 'uuid' })
  guestCartId?: string;

  @ApiProperty({ type: [CartLineItemDto] })
  items!: CartLineItemDto[];

  @ApiProperty()
  subtotalCents!: number;

  @ApiProperty({ example: 'GBP' })
  currency!: string;

  @ApiProperty()
  itemCount!: number;
}
