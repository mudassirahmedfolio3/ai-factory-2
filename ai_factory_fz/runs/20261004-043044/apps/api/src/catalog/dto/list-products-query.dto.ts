import { ApiPropertyOptional } from '@nestjs/swagger';
import { Transform, Type } from 'class-transformer';
import {
  IsArray,
  IsBoolean,
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  MaxLength,
  Min,
} from 'class-validator';
import { PaginationQueryDto } from './pagination-query.dto';

export enum ProductSort {
  PriceAsc = 'priceAsc',
  PriceDesc = 'priceDesc',
  Newest = 'newest',
  Popularity = 'popularity',
}

function toStringArray(value: unknown): string[] | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined;
  }
  return Array.isArray(value) ? value.map(String) : [String(value)];
}

export class ListProductsQueryDto extends PaginationQueryDto {
  @ApiPropertyOptional({ maxLength: 120, description: 'Search name, SKU, brand, description' })
  @IsOptional()
  @IsString()
  @MaxLength(120)
  q?: string;

  @ApiPropertyOptional({ maxLength: 100 })
  @IsOptional()
  @IsString()
  @MaxLength(100)
  categorySlug?: string;

  @ApiPropertyOptional({
    type: [String],
    description: 'Repeat for multiple brands',
  })
  @IsOptional()
  @Transform(({ value }) => toStringArray(value))
  @IsArray()
  @IsString({ each: true })
  @MaxLength(80, { each: true })
  brand?: string[];

  @ApiPropertyOptional({ minimum: 0 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  minPriceCents?: number;

  @ApiPropertyOptional({ minimum: 0 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  maxPriceCents?: number;

  @ApiPropertyOptional({ minimum: 0 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  minWattage?: number;

  @ApiPropertyOptional({ minimum: 0 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  maxWattage?: number;

  @ApiPropertyOptional({ maxLength: 80 })
  @IsOptional()
  @IsString()
  @MaxLength(80)
  finish?: string;

  @ApiPropertyOptional({ default: false })
  @IsOptional()
  @Transform(({ value }) => value === true || value === 'true')
  @IsBoolean()
  inStockOnly: boolean = false;

  @ApiPropertyOptional({ enum: ProductSort, default: ProductSort.Popularity })
  @IsOptional()
  @IsEnum(ProductSort)
  sort: ProductSort = ProductSort.Popularity;
}
