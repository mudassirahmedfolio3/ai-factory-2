import { ApiPropertyOptional } from '@nestjs/swagger';

export class LightingSpecsDto {
  @ApiPropertyOptional({ minimum: 0, example: 24 })
  wattageW?: number;

  @ApiPropertyOptional({ minimum: 0, example: 2400 })
  lumens?: number;

  @ApiPropertyOptional({ example: 3000 })
  colorTemperatureK?: number;

  @ApiPropertyOptional({ example: 'LED' })
  lightType?: string;

  @ApiPropertyOptional({ example: '220-240V' })
  voltage?: string;

  @ApiPropertyOptional()
  dimmable?: boolean;

  @ApiPropertyOptional({ example: 'Aluminum' })
  material?: string;

  @ApiPropertyOptional({ example: 'Matte Black' })
  finish?: string;

  @ApiPropertyOptional({ example: '600x300 mm' })
  dimensionsMm?: string;

  @ApiPropertyOptional({ example: 'IP44' })
  ipRating?: string;

  @ApiPropertyOptional()
  bulbIncluded?: boolean;

  @ApiPropertyOptional({ example: 'Ceiling mounted' })
  installationType?: string;
}
