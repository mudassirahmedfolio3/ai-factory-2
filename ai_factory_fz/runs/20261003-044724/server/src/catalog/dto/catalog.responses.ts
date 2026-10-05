import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export enum AvailabilityStatus {
  IN_STOCK = 'in_stock',
  LOW_STOCK = 'low_stock',
  OUT_OF_STOCK = 'out_of_stock',
}

export class MoneyResponse {
  @ApiProperty({
    example: 1999,
    description: 'Integer minor units (e.g. cents).',
  })
  amountCents!: number;

  @ApiProperty({ example: 'USD', pattern: '^[A-Z]{3}$' })
  currency!: string;
}

export class CategoryResponse {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  slug!: string;

  @ApiProperty()
  name!: string;
}

export class CategoryListResponse {
  @ApiProperty({ type: [CategoryResponse] })
  items!: CategoryResponse[];
}

export class ProductSummaryResponse {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  name!: string;

  @ApiProperty()
  brand!: string;

  @ApiProperty({ type: CategoryResponse })
  category!: CategoryResponse;

  @ApiProperty({ type: MoneyResponse })
  price!: MoneyResponse;

  @ApiProperty({ format: 'uri' })
  primaryImageUrl!: string;

  @ApiProperty({ enum: AvailabilityStatus })
  availability!: AvailabilityStatus;
}

export class ProductListResponse {
  @ApiProperty({ type: [ProductSummaryResponse] })
  items!: ProductSummaryResponse[];

  @ApiProperty({ minimum: 0 })
  total!: number;

  @ApiProperty({ minimum: 1 })
  page!: number;

  @ApiProperty({ minimum: 1 })
  pageSize!: number;
}

export class ProductVariantResponse {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  sku!: string;

  @ApiProperty()
  name!: string;

  @ApiProperty({ type: MoneyResponse })
  price!: MoneyResponse;

  @ApiProperty({ minimum: 0 })
  stockAvailable!: number;

  @ApiPropertyOptional({ format: 'uri' })
  imageUrl?: string;

  @ApiProperty()
  isDefault!: boolean;
}

export class ProductDetailResponse {
  @ApiProperty({ format: 'uuid' })
  id!: string;

  @ApiProperty()
  name!: string;

  @ApiProperty()
  brand!: string;

  @ApiProperty()
  description!: string;

  @ApiProperty({ type: CategoryResponse })
  category!: CategoryResponse;

  @ApiProperty({ type: MoneyResponse })
  price!: MoneyResponse;

  @ApiProperty({ format: 'uri' })
  primaryImageUrl!: string;

  @ApiProperty({ enum: AvailabilityStatus })
  availability!: AvailabilityStatus;

  @ApiProperty({ type: [ProductVariantResponse] })
  variants!: ProductVariantResponse[];
}
