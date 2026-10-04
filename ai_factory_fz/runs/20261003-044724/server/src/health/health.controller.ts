import { Controller, Get } from '@nestjs/common';
import {
  ApiOkResponse,
  ApiOperation,
  ApiServiceUnavailableResponse,
  ApiTags,
} from '@nestjs/swagger';
import { ErrorResponseDto } from '../common/dto/error-response.dto.js';
import { HealthStatusResponse } from './dto/health-status.response.js';
import { HealthService } from './health.service.js';

@ApiTags('Health')
@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get()
  @ApiOperation({
    operationId: 'getHealth',
    summary: 'Liveness/readiness check including database reachability',
  })
  @ApiOkResponse({
    type: HealthStatusResponse,
    description: 'Service and database are healthy',
  })
  @ApiServiceUnavailableResponse({
    type: ErrorResponseDto,
    description: 'Service is unhealthy (e.g. database unreachable)',
  })
  getHealth(): Promise<HealthStatusResponse> {
    return this.healthService.getStatus();
  }
}
