import { Transform } from 'class-transformer';
import {
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  Max,
  MaxLength,
  Min,
} from 'class-validator';

export enum AvailabilityFilter {
  IN_STOCK = 'in_stock',
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
}

export enum ProductSort {
  PRICE_ASC = 'priceAsc',
  PRICE_DESC = 'priceDesc',
  NEWEST = 'newest',
}

const toNumber = ({ value }: { value: unknown }): number | undefined =>
  value === undefined || value === null || value === ''
    ? undefined
    : Number(value);

const emptyToUndefined = ({ value }: { value: unknown }): unknown =>
  value === '' ? undefined : value;

export class ListProductsQueryDto {
  @IsOptional()
  @Transform(emptyToUndefined)
  @IsString()
  @MaxLength(100)
  q?: string;

  @IsOptional()
  @Transform(emptyToUndefined)
  @IsString()
  category?: string;

  @IsOptional()
  @Transform(emptyToUndefined)
  @IsString()
  brand?: string;

  @IsOptional()
  @Transform(toNumber)
  @IsInt()
  @Min(0)
  minPriceCents?: number;

  @IsOptional()
  @Transform(toNumber)
  @IsInt()
  @Min(0)
  maxPriceCents?: number;

  @IsOptional()
  @IsEnum(AvailabilityFilter)
  availability?: AvailabilityFilter;

  @IsOptional()
  @IsEnum(ProductSort)
  sort?: ProductSort;

  @IsOptional()
  @Transform(toNumber)
  @IsInt()
  @Min(1)
  page?: number;

  @IsOptional()
  @Transform(toNumber)
  @IsInt()
  @Min(1)
  @Max(100)
  pageSize?: number;
}
