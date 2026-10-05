import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SupportService } from './support.service.js';

describe('SupportService', () => {
  const prisma = {
    supportMessage: {
      create: vi.fn(),
    },
  };

  let service: SupportService;

  beforeEach(() => {
    vi.resetAllMocks();
    service = new SupportService(prisma as never);
  });

  it('persists message and returns simulated confirmation', async () => {
    prisma.supportMessage.create.mockResolvedValue({
      id: 'msg-1',
      email: 'a@b.com',
      subject: 'Help',
      body: 'Issue',
      orderNumber: null,
      userId: null,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    const result = await service.submitMessage({
      email: 'a@b.com',
      subject: 'Help',
      body: 'Issue',
    });

    expect(result.id).toBe('msg-1');
    expect(result.message).toContain('one to two business days');
    expect(prisma.supportMessage.create).toHaveBeenCalled();
  });
});
