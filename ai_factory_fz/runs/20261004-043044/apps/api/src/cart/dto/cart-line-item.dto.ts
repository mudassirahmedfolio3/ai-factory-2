import { ApiProperty } from '@nestjs/swagger';
import { MoneyDto } from '../../catalog/dto/money.dto';

export class CartLineItemDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ format: 'uuid' })
  variantId!: string;

  @ApiProperty({ format: 'uuid' })
  productId!: string;

  @ApiProperty()
  productName!: string;

  @ApiProperty()
  variantLabel!: string;

  @ApiProperty()
  sku!: string;

  @ApiProperty()
  quantity!: number;

  @ApiProperty({ type: MoneyDto })
  unitPrice!: MoneyDto;

  @ApiProperty()
  lineSubtotalCents!: number;

  @ApiProperty()
  imageUrl!: string;
}
