import { ApiProperty } from '@nestjs/swagger';
import { ProductSummaryDto } from '../../catalog/dto/product-summary.dto';

export class WishlistItemDto {
  @ApiProperty({ format: 'uuid' })
  productId!: string;

  @ApiProperty({ format: 'date-time' })
  addedAt!: string;

  @ApiProperty({ type: ProductSummaryDto })
  product!: ProductSummaryDto;
}
