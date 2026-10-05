import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsInt,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  Min,
  ValidateNested,
} from 'class-validator';
import { CartLineInputDto } from '../../cart/dto/cart.dto.js';
import { MoneyResponse } from '../../catalog/dto/catalog.responses.js';
import { ShippingAddressDto } from '../../checkout/dto/checkout.dto.js';

export enum ShopperOrderStatus {
  AWAITING_PAYMENT = 'awaiting_payment',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded',
}

export enum BackendOrderStatus {
  PENDING_PAYMENT = 'pending_payment',
  PAID = 'paid',
  FULFILLED = 'fulfilled',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
  REFUNDED = 'refunded',
}

export class CreateOrderRequestDto {
  @ApiProperty({ type: ShippingAddressDto })
  @ValidateNested()
  @Type(() => ShippingAddressDto)
  shippingAddress!: ShippingAddressDto;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(32)
  couponCode?: string;

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

  @ApiProperty({ maxLength: 64 })
  @IsString()
  @MaxLength(64)
  idempotencyKey!: string;
}

export class OrderSummaryDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  orderNumber!: string;

  @ApiProperty({ format: 'date-time' })
  createdAt!: string;

  @ApiProperty({ type: MoneyResponse })
  total!: MoneyResponse;

  @ApiProperty({ enum: ShopperOrderStatus })
  shopperStatus!: ShopperOrderStatus;
}

export class OrderListResponseDto {
  @ApiProperty({ type: [OrderSummaryDto] })
  items!: OrderSummaryDto[];

  @ApiProperty()
  total!: number;

  @ApiProperty()
  page!: number;

  @ApiProperty()
  pageSize!: number;
}

export class OrderLineItemDto {
  @ApiProperty()
  productName!: string;

  @ApiProperty()
  variantName!: string;

  @ApiProperty()
  sku!: string;

  @ApiProperty()
  quantity!: number;

  @ApiProperty({ type: MoneyResponse })
  unitPrice!: MoneyResponse;

  @ApiProperty({ type: MoneyResponse })
  lineTotal!: MoneyResponse;
}

export class OrderDetailDto {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  orderNumber!: string;

  @ApiProperty({ format: 'date-time' })
  createdAt!: string;

  @ApiProperty({ enum: ShopperOrderStatus })
  shopperStatus!: ShopperOrderStatus;

  @ApiProperty({ enum: BackendOrderStatus })
  backendStatus!: BackendOrderStatus;

  @ApiProperty({ type: [OrderLineItemDto] })
  lines!: OrderLineItemDto[];

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

  @ApiPropertyOptional()
  couponCode?: string;

  @ApiProperty({ type: ShippingAddressDto })
  shippingAddress!: ShippingAddressDto;

  @ApiPropertyOptional()
  carrierName?: string;

  @ApiPropertyOptional()
  trackingNumber?: string;
}

export class ListOrdersQueryDto {
  @ApiPropertyOptional({ default: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number;

  @ApiPropertyOptional({ default: 20 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  pageSize?: number;
}
