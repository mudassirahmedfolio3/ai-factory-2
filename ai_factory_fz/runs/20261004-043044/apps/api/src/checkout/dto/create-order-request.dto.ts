import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsEmail, IsOptional, IsString, MinLength, ValidateNested } from 'class-validator';
import { UkAddressInputDto } from './uk-address-input.dto';

export class CreateOrderRequestDto {
  @ApiProperty({ type: UkAddressInputDto })
  @ValidateNested()
  @Type(() => UkAddressInputDto)
  shippingAddress!: UkAddressInputDto;

  @ApiProperty({ format: 'email' })
  @IsEmail()
  contactEmail!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MinLength(1)
  couponCode?: string;
}
