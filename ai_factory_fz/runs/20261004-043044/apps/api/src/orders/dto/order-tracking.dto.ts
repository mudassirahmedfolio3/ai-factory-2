import { ApiPropertyOptional } from '@nestjs/swagger';

export class OrderTrackingDto {
  @ApiPropertyOptional()
  carrierName?: string;

  @ApiPropertyOptional()
  trackingNumber?: string;

  @ApiPropertyOptional()
  estimatedDeliveryCopy?: string;
}
