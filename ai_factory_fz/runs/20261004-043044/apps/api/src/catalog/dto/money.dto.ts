import { ApiProperty } from '@nestjs/swagger';

export class MoneyDto {
  @ApiProperty({ minimum: 0, example: 4999, description: 'Pence for GBP' })
  amountCents!: number;

  @ApiProperty({ pattern: '^[A-Z]{3}$', example: 'GBP' })
  currency!: string;
}
