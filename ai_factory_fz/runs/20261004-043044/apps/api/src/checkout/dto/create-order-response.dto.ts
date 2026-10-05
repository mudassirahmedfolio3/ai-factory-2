import { ApiProperty } from '@nestjs/swagger';

export class CreateOrderResponseDto {
  @ApiProperty({ format: 'uuid' })
  orderId!: string;

  @ApiProperty()
  orderNumber!: string;

  @ApiProperty({ enum: ['pending_payment'] })
  status!: 'pending_payment';

  @ApiProperty()
  totalCents!: number;

  @ApiProperty()
  currency!: string;

  @ApiProperty({ format: 'uuid' })
  mockPaymentSessionId!: string;

  @ApiProperty({ format: 'date-time' })
  paymentExpiresAt!: string;
}
