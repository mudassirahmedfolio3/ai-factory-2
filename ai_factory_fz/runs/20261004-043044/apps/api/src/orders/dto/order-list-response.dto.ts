import { ApiProperty } from '@nestjs/swagger';
import { OrderSummaryDto } from './order-summary.dto';

export class OrderListResponseDto {
  @ApiProperty({ type: [OrderSummaryDto] })
  items!: OrderSummaryDto[];

  @ApiProperty()
  total!: number;

  @ApiProperty({ minimum: 1 })
  page!: number;

  @ApiProperty({ minimum: 1, maximum: 50 })
  pageSize!: number;
}
