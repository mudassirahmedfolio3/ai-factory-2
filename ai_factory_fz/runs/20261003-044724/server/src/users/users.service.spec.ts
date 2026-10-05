import { beforeEach, describe, expect, it, vi } from 'vitest';
import { UsersService } from './users.service.js';

describe('UsersService', () => {
  const prisma = {
    user: {
      findUnique: vi.fn(),
      update: vi.fn(),
    },
    passwordResetToken: {
      updateMany: vi.fn(),
    },
    $transaction: vi.fn(),
  };

  const authService = {
    revokeAllRefreshTokensForUser: vi.fn(),
  };

  let service: UsersService;

  beforeEach(() => {
    vi.resetAllMocks();
    prisma.$transaction.mockImplementation((ops: unknown[]) => Promise.all(ops));
    service = new UsersService(prisma as never, authService as never);
  });

  it('soft-deletes the user, anonymizes email, and revokes tokens', async () => {
    prisma.user.findUnique.mockResolvedValue({
      id: 'user-123',
      email: 'shopper@example.com',
      deletedAt: null,
    });
    prisma.passwordResetToken.updateMany.mockResolvedValue({ count: 0 });
    prisma.user.update.mockResolvedValue({});

    await service.deleteAccount('user-123');

    expect(authService.revokeAllRefreshTokensForUser).toHaveBeenCalledWith(
      'user-123',
    );
    expect(prisma.user.update).toHaveBeenCalledWith({
      where: { id: 'user-123' },
      data: expect.objectContaining({
        deletedAt: expect.any(Date),
        email: 'deleted+user-123@deleted.local',
        displayName: null,
        passwordHash: expect.any(String),
      }),
    });
  });

  it('no-ops when user is already deleted', async () => {
    prisma.user.findUnique.mockResolvedValue({
      id: 'user-123',
      deletedAt: new Date(),
    });

    await service.deleteAccount('user-123');

    expect(authService.revokeAllRefreshTokensForUser).not.toHaveBeenCalled();
    expect(prisma.$transaction).not.toHaveBeenCalled();
  });
});
