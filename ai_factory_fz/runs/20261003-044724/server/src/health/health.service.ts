import {
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service.js';
import type { HealthStatusResponse } from './dto/health-status.response.js';

@Injectable()
export class HealthService {
  constructor(private readonly prisma: PrismaService) {}

  async getStatus(): Promise<HealthStatusResponse> {
    const timestamp = new Date().toISOString();
    try {
      await this.prisma.$queryRawUnsafe('SELECT 1');
      return { status: 'ok', database: 'up', timestamp };
    } catch {
      throw new ServiceUnavailableException('Database is unreachable');
    }
  }
}
