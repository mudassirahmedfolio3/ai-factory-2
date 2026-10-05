import { ApiProperty } from '@nestjs/swagger';
import { IsUUID } from 'class-validator';

export class AddWishlistItemRequestDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID()
  productId!: string;
}
