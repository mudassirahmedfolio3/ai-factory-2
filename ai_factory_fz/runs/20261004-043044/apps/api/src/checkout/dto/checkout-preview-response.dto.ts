import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CheckoutPreviewResponseDto {
  @ApiProperty()
  subtotalCents!: number;

  @ApiProperty()
  shippingCents!: number;

  @ApiProperty()
  discountCents!: number;

  @ApiProperty()
  totalCents!: number;

  @ApiProperty()
  currency!: string;

  @ApiProperty()
  shippingLabel!: string;

  @ApiProperty({ example: 7500 })
  freeDeliveryThresholdCents!: number;

  @ApiProperty()
  couponApplied!: boolean;

  @ApiPropertyOptional()
  couponCode?: string;

  @ApiPropertyOptional()
  couponMessage?: string;
}
