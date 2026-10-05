import { ApiProperty } from '@nestjs/swagger';

export class MockPaymentConfirmResponseDto {
  @ApiProperty({ format: 'uuid' })
  orderId!: string;

  @ApiProperty()
  orderNumber!: string;

  @ApiProperty({ enum: ['paid', 'pending_payment', 'cancelled'] })
  status!: 'paid' | 'pending_payment' | 'cancelled';

  @ApiProperty({ format: 'date-time' })
  paidAt!: string;
}
