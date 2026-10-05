import { Controller, Get } from '@nestjs/common';
import {
  ApiOperation,
  ApiResponse,
  ApiTags,
} from '@nestjs/swagger';
import { HealthResponseDto } from './dto/health-response.dto';
import { HealthService } from './health.service';

@ApiTags('Health')
@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get()
  @ApiOperation({
    operationId: 'getHealth',
    summary: 'Health check',
    description:
      'Returns 200 when the API process and PostgreSQL are reachable.',
  })
  @ApiResponse({ status: 200, type: HealthResponseDto })
  @ApiResponse({
    status: 503,
    description: 'Database unreachable',
  })
  getHealth(): Promise<HealthResponseDto> {
    return this.healthService.getHealth();
  }
}
