import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class HomeBannerDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ example: 'Winter Lighting Sale' })
  title!: string;

  @ApiPropertyOptional({ example: 'Save on ceiling fixtures' })
  subtitle?: string;

  @ApiProperty({ format: 'uri' })
  imageUrl!: string;

  @ApiProperty({ example: 'Shop now' })
  ctaLabel!: string;

  @ApiPropertyOptional({ example: 'ceiling-lights' })
  categorySlug?: string;
}
