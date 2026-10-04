jest.mock('@nestjs/common', () => ({
  Injectable: () => (target: unknown) => target,
  ServiceUnavailableException: class ServiceUnavailableException extends Error {
    response: unknown;
    constructor(response: unknown) {
      super('Service Unavailable');
      this.response = response;
    }
  },
}));

import { ServiceUnavailableException } from '@nestjs/common';
import { HealthService } from './health.service';

describe('HealthService', () => {
  let service: HealthService;
  let prisma: { pingDatabase: jest.Mock };

  beforeEach(() => {
    prisma = { pingDatabase: jest.fn() };
    service = new HealthService(prisma as never);
  });

  it('returns ok when database responds', async () => {
    prisma.pingDatabase.mockResolvedValue(undefined);
    const result = await service.getHealth();
    expect(result.status).toBe('ok');
    expect(result.database).toBe('up');
    expect(result.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('throws 503 when database is unreachable', async () => {
    prisma.pingDatabase.mockRejectedValue(new Error('connection refused'));
    await expect(service.getHealth()).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });
});
