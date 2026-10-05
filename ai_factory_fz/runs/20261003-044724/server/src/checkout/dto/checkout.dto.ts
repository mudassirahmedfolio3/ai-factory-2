import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsEmail,
  IsEnum,
  IsOptional,
  IsString,
  MaxLength,
  ValidateNested,
} from 'class-validator';
import { CartItemResponseDto, CartLineInputDto } from '../../cart/dto/cart.dto.js';
import { MoneyResponse } from '../../catalog/dto/catalog.responses.js';

export enum CouponRejectionReason {
  INVALID = 'invalid',
  EXPIRED = 'expired',
  MINIMUM_NOT_MET = 'minimum_not_met',
  EXCLUDED_ITEMS = 'excluded_items',
  ALREADY_APPLIED = 'already_applied',
}

export class ShippingAddressDto {
  @ApiProperty()
  @IsString()
  @MaxLength(100)
  fullName!: string;

  @ApiPropertyOptional({ format: 'email' })
  @IsOptional()
  @IsEmail()
  email?: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(30)
  phone?: string;

  @ApiProperty()
  @IsString()
  @MaxLength(200)
  line1!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(200)
  line2?: string;

  @ApiProperty()
  @IsString()
  @MaxLength(100)
  city!: string;

  @ApiProperty({ description: 'US state code' })
  @IsString()
  @MaxLength(100)
  region!: string;

  @ApiProperty()
  @IsString()
  @MaxLength(20)
  postalCode!: string;

  @ApiProperty({ enum: ['US'] })
  @IsString()
  country!: 'US';
}

export class CouponValidationDto {
  @ApiProperty()
  valid!: boolean;

  @ApiPropertyOptional()
  code?: string;

  @ApiPropertyOptional({ enum: CouponRejectionReason })
  @IsOptional()
  @IsEnum(CouponRejectionReason)
  rejectionReason?: CouponRejectionReason;

  @ApiPropertyOptional({ type: MoneyResponse })
  discount?: MoneyResponse;
}

export class CheckoutQuoteRequestDto {
  @ApiPropertyOptional({ default: true })
  @IsOptional()
  @IsBoolean()
  useServerCart?: boolean;

  @ApiPropertyOptional({ type: [CartLineInputDto] })
  @IsOptional()
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CartLineInputDto)
  lines?: CartLineInputDto[];

  @ApiProperty({ type: ShippingAddressDto })
  @ValidateNested()
  @Type(() => ShippingAddressDto)
  shippingAddress!: ShippingAddressDto;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(32)
  couponCode?: string;
}

export class CheckoutQuoteResponseDto {
  @ApiProperty({ type: [CartItemResponseDto] })
  lines!: CartItemResponseDto[];

  @ApiProperty({ type: MoneyResponse })
  subtotal!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  discount!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  shipping!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  tax!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  total!: MoneyResponse;

  @ApiProperty({ type: CouponValidationDto })
  coupon!: CouponValidationDto;

  @ApiPropertyOptional()
  taxDisclaimer?: string;
}
