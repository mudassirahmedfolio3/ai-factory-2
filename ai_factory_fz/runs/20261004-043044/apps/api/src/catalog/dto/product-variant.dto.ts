import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { MoneyDto } from './money.dto';

export class ProductVariantDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ example: 'CL-1001-BK' })
  sku!: string;

  @ApiProperty({ example: 'Matte Black / 3000K / 24W' })
  label!: string;

  @ApiProperty({ type: MoneyDto })
  price!: MoneyDto;

  @ApiPropertyOptional({ type: MoneyDto, nullable: true })
  compareAtPrice?: MoneyDto | null;

  @ApiProperty({ minimum: 0 })
  stockQuantity!: number;

  @ApiProperty({ minimum: 0, description: 'stockQuantity minus active reservations' })
  availableQuantity!: number;

  @ApiPropertyOptional()
  finish?: string;

  @ApiPropertyOptional()
  wattageW?: number;

  @ApiPropertyOptional()
  colorTemperatureK?: number;

  @ApiPropertyOptional({ format: 'uri' })
  imageUrl?: string;

  @ApiProperty()
  isDefault!: boolean;
}
