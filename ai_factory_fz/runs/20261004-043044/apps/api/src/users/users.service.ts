import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { UserProfileDto } from './dto/user-profile.dto';
import { toUserProfile } from './user.mapper';

@Injectable()
export class UsersService {
  constructor(private readonly prisma: PrismaService) {}

  getCurrentUser(userId: string): Promise<UserProfileDto> {
    return this.prisma.user
      .findFirstOrThrow({
        where: { id: userId, deletedAt: null },
        select: { id: true, email: true, displayName: true },
      })
      .then(toUserProfile);
  }

  async deleteCurrentUser(userId: string): Promise<void> {
    const now = new Date();
    const anonymizedEmail = `deleted+${userId}@deleted.invalid`;

    await this.prisma.$transaction([
      this.prisma.refreshToken.updateMany({
        where: { userId, revokedAt: null },
        data: { revokedAt: now },
      }),
      this.prisma.user.update({
        where: { id: userId },
        data: {
          deletedAt: now,
          email: anonymizedEmail,
          passwordHash: null,
          displayName: null,
        },
      }),
    ]);
  }
}
