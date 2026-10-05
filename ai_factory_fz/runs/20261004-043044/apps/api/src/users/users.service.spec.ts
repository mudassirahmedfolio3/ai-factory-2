import { Test, TestingModule } from '@nestjs/testing';
import { PrismaService } from '../prisma/prisma.service';
import { UsersService } from './users.service';

describe('UsersService', () => {
  let service: UsersService;
  let prisma: {
    user: { findFirstOrThrow: jest.Mock; update: jest.Mock };
    refreshToken: { updateMany: jest.Mock };
    $transaction: jest.Mock;
  };

  const userId = '11111111-1111-4111-8111-111111111111';

  beforeEach(async () => {
    prisma = {
      user: {
        findFirstOrThrow: jest.fn(),
        update: jest.fn(),
      },
      refreshToken: {
        updateMany: jest.fn(),
      },
      $transaction: jest.fn((ops: unknown[]) => Promise.all(ops)),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [UsersService, { provide: PrismaService, useValue: prisma }],
    }).compile();

    service = module.get(UsersService);
  });

  describe('getCurrentUser', () => {
    it('maps the active user to UserProfile', async () => {
      prisma.user.findFirstOrThrow.mockResolvedValue({
        id: userId,
        email: 'shopper@example.com',
        displayName: 'Alex Morgan',
      });

      await expect(service.getCurrentUser(userId)).resolves.toEqual({
        id: userId,
        email: 'shopper@example.com',
        displayName: 'Alex Morgan',
      });
    });
  });

  describe('deleteCurrentUser', () => {
    it('soft-deletes and anonymizes PII while revoking refresh tokens', async () => {
      await service.deleteCurrentUser(userId);

      expect(prisma.$transaction).toHaveBeenCalled();
      expect(prisma.refreshToken.updateMany).toHaveBeenCalledWith({
        where: { userId, revokedAt: null },
        data: { revokedAt: expect.any(Date) },
      });
      expect(prisma.user.update).toHaveBeenCalledWith({
        where: { id: userId },
        data: {
          deletedAt: expect.any(Date),
          email: `deleted+${userId}@deleted.invalid`,
          passwordHash: null,
          displayName: null,
        },
      });
    });
  });
});
