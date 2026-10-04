export type HealthStatus = 'ok' | 'degraded';
export type DatabaseStatus = 'up' | 'down';

export class HealthResponseDto {
  status!: HealthStatus;
  database!: DatabaseStatus;
  timestamp!: string;
}
