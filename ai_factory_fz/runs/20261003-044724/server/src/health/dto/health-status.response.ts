import { ApiProperty } from '@nestjs/swagger';

export class HealthStatusResponse {
  @ApiProperty({ enum: ['ok', 'degraded'] })
  status!: 'ok' | 'degraded';

  @ApiProperty({ enum: ['up', 'down'] })
  database!: 'up' | 'down';

  @ApiProperty({ type: String, format: 'date-time' })
  timestamp!: string;
}
