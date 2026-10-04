jest.mock('@nestjs/common', () => ({
  Controller: () => (target: unknown) => target,
  Get: () => () => undefined,
  Injectable: () => (target: unknown) => target,
  ServiceUnavailableException: class ServiceUnavailableException extends Error {
    response: unknown;
    constructor(response: unknown) {
      super('Service Unavailable');
      this.response = response;
    }
  },
}));

import { HealthController } from './health.controller';
import { HealthService } from './health.service';

describe('HealthController', () => {
  it('delegates to HealthService.getHealth', async () => {
    const payload = {
      status: 'ok' as const,
      database: 'up' as const,
      timestamp: '2026-10-04T12:00:00.000Z',
    };
    const healthService = {
      getHealth: jest.fn().mockResolvedValue(payload),
    };
    const controller = new HealthController(healthService as unknown as HealthService);

    await expect(controller.getHealth()).resolves.toEqual(payload);
    expect(healthService.getHealth).toHaveBeenCalledTimes(1);
  });
});
