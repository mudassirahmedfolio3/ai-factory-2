import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class CategorySummaryDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ example: 'Ceiling Lights' })
  name!: string;

  @ApiProperty({ example: 'ceiling-lights' })
  slug!: string;

  @ApiPropertyOptional({ format: 'uuid', nullable: true })
  parentId?: string | null;

  @ApiPropertyOptional({ format: 'uri' })
  imageUrl?: string;
}
