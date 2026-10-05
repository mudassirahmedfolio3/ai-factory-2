import { ApiProperty } from '@nestjs/swagger';
import { IsIn, IsUUID } from 'class-validator';

export class MockPaymentConfirmRequestDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID()
  orderId!: string;

  @ApiProperty({ format: 'uuid' })
  @IsUUID()
  mockPaymentSessionId!: string;

  @ApiProperty({ enum: ['success', 'failure', 'cancel'] })
  @IsIn(['success', 'failure', 'cancel'])
  outcome!: 'success' | 'failure' | 'cancel';
}
