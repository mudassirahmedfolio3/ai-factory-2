import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  ArrayNotEmpty,
  IsArray,
  IsEnum,
  IsInt,
  IsOptional,
  IsUUID,
  Min,
  ValidateNested,
} from 'class-validator';
import { MoneyResponse } from '../../catalog/dto/catalog.responses.js';

export class CartLineInputDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID()
  variantId!: string;

  @ApiProperty({ minimum: 1 })
  @IsInt()
  @Min(1)
  quantity!: number;
}

export class ReplaceCartRequestDto {
  @ApiProperty({ type: [CartLineInputDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CartLineInputDto)
  items!: CartLineInputDto[];
}

export enum MergeCartStrategy {
  MERGE = 'merge',
  GUEST_WINS = 'guest_wins',
}

export class MergeCartRequestDto {
  @ApiProperty({ type: [CartLineInputDto] })
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CartLineInputDto)
  guestItems!: CartLineInputDto[];

  @ApiPropertyOptional({
    enum: MergeCartStrategy,
    default: MergeCartStrategy.MERGE,
  })
  @IsOptional()
  @IsEnum(MergeCartStrategy)
  strategy?: MergeCartStrategy;
}

export class CartItemResponseDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty({ format: 'uuid' })
  variantId!: string;

  @ApiProperty({ format: 'uuid' })
  productId!: string;

  @ApiProperty()
  productName!: string;

  @ApiProperty()
  variantName!: string;

  @ApiProperty()
  quantity!: number;

  @ApiProperty({ type: MoneyResponse })
  unitPrice!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  lineTotal!: MoneyResponse;
}

export class CartResponseDto {
  @ApiProperty({ type: [CartItemResponseDto] })
  items!: CartItemResponseDto[];

  @ApiProperty({ type: MoneyResponse })
  subtotal!: MoneyResponse;
}
