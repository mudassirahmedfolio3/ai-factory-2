import { Controller, Get } from '@nestjs/common';
import { HealthResponseDto } from './dto/health-response.dto';
import { HealthService } from './health.service';

@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get()
  getHealth(): Promise<HealthResponseDto> {
    return this.healthService.getHealth();
  }
}
