import { Injectable } from '@nestjs/common';
import * as bcrypt from 'bcrypt';
import { randomBytes } from 'node:crypto';
import { AuthService } from '../auth/auth.service.js';
import { PrismaService } from '../prisma/prisma.service.js';

@Injectable()
export class UsersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly authService: AuthService,
  ) {}

  async deleteAccount(userId: string): Promise<void> {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
    });
    if (user === null || user.deletedAt !== null) {
      return;
    }

    const anonymizedEmail = `deleted+${userId}@deleted.local`;
    const unusableHash = await bcrypt.hash(
      randomBytes(32).toString('hex'),
      12,
    );

    await this.authService.revokeAllRefreshTokensForUser(userId);

    await this.prisma.$transaction([
      this.prisma.passwordResetToken.updateMany({
        where: { userId, usedAt: null },
        data: { usedAt: new Date() },
      }),
      this.prisma.user.update({
        where: { id: userId },
        data: {
          deletedAt: new Date(),
          email: anonymizedEmail,
          displayName: null,
          passwordHash: unusableHash,
        },
      }),
    ]);
  }
}
