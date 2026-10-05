import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class ProductImageDto {
  @ApiProperty({ format: 'uri' })
  url!: string;

  @ApiPropertyOptional()
  altText?: string;

  @ApiProperty({ minimum: 0 })
  sortOrder!: number;
}
