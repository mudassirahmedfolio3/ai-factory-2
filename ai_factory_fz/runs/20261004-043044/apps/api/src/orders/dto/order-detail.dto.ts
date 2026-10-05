import { ApiProperty } from '@nestjs/swagger';
import { UkAddressInputDto } from '../../checkout/dto/uk-address-input.dto';
import { OrderLineItemDto } from './order-line-item.dto';
import { OrderSummaryDto } from './order-summary.dto';
import { OrderTrackingDto } from './order-tracking.dto';

export class OrderDetailDto extends OrderSummaryDto {
  @ApiProperty({ type: [OrderLineItemDto] })
  items!: OrderLineItemDto[];

  @ApiProperty()
  subtotalCents!: number;

  @ApiProperty()
  shippingCents!: number;

  @ApiProperty()
  discountCents!: number;

  @ApiProperty({ type: UkAddressInputDto })
  shippingAddress!: UkAddressInputDto;

  @ApiProperty({ type: OrderTrackingDto })
  tracking!: OrderTrackingDto;
}
