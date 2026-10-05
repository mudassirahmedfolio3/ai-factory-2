import { ApiProperty } from '@nestjs/swagger';

export class UserProfileDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ example: 'shopper@example.com' })
  email!: string;

  @ApiProperty({ example: 'Alex Morgan' })
  displayName!: string;
}
