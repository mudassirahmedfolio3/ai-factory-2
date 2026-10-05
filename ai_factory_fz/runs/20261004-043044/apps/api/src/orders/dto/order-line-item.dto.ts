import { ApiProperty } from '@nestjs/swagger';

export class OrderLineItemDto {
  @ApiProperty()
  productName!: string;

  @ApiProperty()
  variantLabel!: string;

  @ApiProperty()
  sku!: string;

  @ApiProperty()
  quantity!: number;

  @ApiProperty()
  unitPriceCents!: number;

  @ApiProperty()
  lineTotalCents!: number;

  @ApiProperty({ example: 'GBP' })
  currency!: string;
}
