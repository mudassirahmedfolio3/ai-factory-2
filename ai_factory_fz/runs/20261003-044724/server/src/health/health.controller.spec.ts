import { ServiceUnavailableException } from '@nestjs/common';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { HealthController } from './health.controller.js';
import { HealthService } from './health.service.js';

describe('HealthController', () => {
  const healthService = {
    getStatus: vi.fn(),
  };
  let controller: HealthController;

  beforeEach(() => {
    vi.resetAllMocks();
    controller = new HealthController(healthService as unknown as HealthService);
  });

  it('returns the health status from the service', async () => {
    healthService.getStatus.mockResolvedValue({
      status: 'ok',
      database: 'up',
      timestamp: '2026-10-04T00:00:00.000Z',
    });

    await expect(controller.getHealth()).resolves.toEqual({
      status: 'ok',
      database: 'up',
      timestamp: '2026-10-04T00:00:00.000Z',
    });
    expect(healthService.getStatus).toHaveBeenCalledTimes(1);
  });

  it('propagates ServiceUnavailableException when database is down (503 contract)', async () => {
    healthService.getStatus.mockRejectedValue(
      new ServiceUnavailableException('Database is unreachable'),
    );

    await expect(controller.getHealth()).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });
});
