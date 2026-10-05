import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsIn, IsOptional, IsString, MinLength } from 'class-validator';

export class UkAddressInputDto {
  @ApiProperty()
  @IsString()
  @MinLength(1)
  fullName!: string;

  @ApiProperty()
  @IsString()
  @MinLength(1)
  line1!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  line2?: string;

  @ApiProperty()
  @IsString()
  @MinLength(1)
  city!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  region?: string;

  @ApiProperty()
  @IsString()
  @MinLength(1)
  postalCode!: string;

  @ApiProperty({ enum: ['GB'] })
  @IsIn(['GB'])
  country!: 'GB';
}
