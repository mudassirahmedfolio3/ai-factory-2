import { ServiceUnavailableException } from '@nestjs/common';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { HealthService } from './health.service.js';

describe('HealthService', () => {
  const prisma = {
    $queryRawUnsafe: vi.fn(),
  };
  let service: HealthService;

  beforeEach(() => {
    vi.resetAllMocks();
    service = new HealthService(prisma as never);
  });

  it('returns ok when the database responds', async () => {
    prisma.$queryRawUnsafe.mockResolvedValue([{ '?column?': 1 }]);
    const result = await service.getStatus();
    expect(result.status).toBe('ok');
    expect(result.database).toBe('up');
    expect(result.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('throws 503 when the database is unreachable', async () => {
    prisma.$queryRawUnsafe.mockRejectedValue(new Error('connection refused'));
    await expect(service.getStatus()).rejects.toBeInstanceOf(
      ServiceUnavailableException,
    );
  });
});
