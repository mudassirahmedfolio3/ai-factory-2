import { User } from '@prisma/client';
import { UserProfileDto } from './dto/user-profile.dto';

export function toUserProfile(user: Pick<User, 'id' | 'email' | 'displayName'>): UserProfileDto {
  return {
    id: user.id,
    email: user.email,
    displayName: user.displayName ?? '',
  };
}
