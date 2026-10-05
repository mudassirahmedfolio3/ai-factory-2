import { ApiProperty } from '@nestjs/swagger';
import { OrderStatus } from '@prisma/client';

const ORDER_STATUS_VALUES = Object.values(OrderStatus);

export class OrderSummaryDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  orderNumber!: string;

  @ApiProperty({ enum: ORDER_STATUS_VALUES })
  status!: OrderStatus;

  @ApiProperty()
  customerStatusLabel!: string;

  @ApiProperty()
  totalCents!: number;

  @ApiProperty({ example: 'GBP' })
  currency!: string;

  @ApiProperty({ format: 'date-time' })
  createdAt!: string;
}
