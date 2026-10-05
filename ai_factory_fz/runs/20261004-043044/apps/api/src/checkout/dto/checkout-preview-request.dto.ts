import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsOptional, IsString, MinLength, ValidateNested } from 'class-validator';
import { UkAddressInputDto } from './uk-address-input.dto';

export class CheckoutPreviewRequestDto {
  @ApiProperty({ type: UkAddressInputDto })
  @ValidateNested()
  @Type(() => UkAddressInputDto)
  shippingAddress!: UkAddressInputDto;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MinLength(1)
  couponCode?: string;
}
