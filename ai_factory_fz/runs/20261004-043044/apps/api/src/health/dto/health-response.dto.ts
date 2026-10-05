import { ApiProperty } from '@nestjs/swagger';

export type HealthStatus = 'ok' | 'degraded';
export type DatabaseStatus = 'up' | 'down';

export class HealthResponseDto {
  @ApiProperty({ enum: ['ok', 'degraded'], example: 'ok' })
  status!: HealthStatus;

  @ApiProperty({ enum: ['up', 'down'], example: 'up' })
  database!: DatabaseStatus;

  @ApiProperty({ format: 'date-time', example: '2026-10-04T12:00:00.000Z' })
  timestamp!: string;
}
